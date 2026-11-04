import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mongomock_motor import AsyncMongoMockClient
from beanie import init_beanie
from app.models import (
    User, Client, Requisition, Candidate, Submission, AuditLog,
    UserRole, PipelineStage, ClientDecision, ScorecardCriterion, ConsentRecord
)
from app.auth import hash_password, verify_password, create_token
from app.ai.jd_extractor import extract_scorecard_from_jd
from app.ai.cv_parser import extract_profile_and_blind_text
from app.ai.scorer import score_candidate
from app.main import app

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_staffing_db"],
        document_models=[User, Client, Requisition, Candidate, Submission, AuditLog]
    )
    yield
    # Cleanup collections
    await User.get_motor_collection().drop()
    await Client.get_motor_collection().drop()
    await Requisition.get_motor_collection().drop()
    await Candidate.get_motor_collection().drop()
    await Submission.get_motor_collection().drop()
    await AuditLog.get_motor_collection().drop()

@pytest.mark.asyncio
async def test_password_hashing():
    pw = "SuperSecret123!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

@pytest.mark.asyncio
async def test_jd_extractor():
    jd = """
    We are looking for a Senior Python Developer.
    Requirements:
    - 4-6 years of experience in Python and Django
    - Must have Docker and PostgreSQL experience
    - Notice period: 30 days
    - CTC: 18-24 LPA
    """
    criteria = extract_scorecard_from_jd(jd)
    names = [c.name.lower() for c in criteria]
    assert any("experience" in n for n in names)
    assert any("notice" in n for n in names)
    assert any("ctc" in n for n in names)
    assert any("python" in n for n in names)
    assert any("django" in n for n in names)
    assert any("docker" in n for n in names)

@pytest.mark.asyncio
async def test_cv_parser_and_blind_text():
    cv = """
    Jane Smith
    Email: jane.smith@example.com
    Phone: 9876543210
    DOB: 10/10/1995
    Gender: Female
    Marital Status: Married
    Current Role: Senior Backend Engineer
    Total Experience: 5 years
    Notice period: 15 days
    Skills: Python, Django, FastAPI, Docker
    Built robust REST APIs using Python and Django.
    """
    profile, blind_text, err = extract_profile_and_blind_text(cv, "jane_resume.txt")
    assert err is None
    assert profile["full_name"] == "Jane Smith"
    assert profile["email"] == "jane.smith@example.com"
    assert profile["phone"] == "9876543210"
    assert profile["experience_years"] == 5.0
    assert profile["notice_days"] == 15
    assert "Python" in profile["skills"]

    # Blind text checks
    assert "Jane Smith" not in blind_text
    assert "Female" not in blind_text
    assert "Married" not in blind_text
    assert "jane.smith@example.com" not in blind_text

@pytest.mark.asyncio
async def test_scorer_with_quotes():
    criteria = [
        ScorecardCriterion(name="Python", type="skill", weight=1.0, required=True),
        ScorecardCriterion(name="5+ years experience", type="experience", weight=1.5, required=True),
        ScorecardCriterion(name="Notice period", type="notice", weight=1.0, required=False),
    ]
    cand = Candidate(
        full_name="Bob Test",
        email="bob@example.com",
        phone="9123456789",
        current_role="Developer",
        experience_years=6.0,
        skills=["Python"],
        notice_days=20,
        raw_text="Bob Test\nTotal Experience: 6 years\nNotice: 20 days\nWorked with Python daily.",
        blind_text="[Candidate]\nTotal Experience: 6 years\nNotice: 20 days\nWorked with Python daily.",
        fingerprint="fp123"
    )
    evidences, score = score_candidate(cand, criteria)
    assert score > 80.0
    python_ev = next(e for e in evidences if e.criterion_name == "Python")
    assert python_ev.matched is True
    assert python_ev.score == 1.0
    assert len(python_ev.evidence_quotes) > 0

@pytest.mark.asyncio
async def test_full_api_workflow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create client and users
        client = Client(name="Acme Corp", contact_email="contact@acme.com")
        await client.insert()

        recruiter = User(
            email="recruiter@staffing.com",
            hashed_password=hash_password("recruiter123"),
            full_name="Alice Recruiter",
            role=UserRole.recruiter,
            is_active=True
        )
        await recruiter.insert()

        hiring_mgr = User(
            email="client@acme.com",
            hashed_password=hash_password("client123"),
            full_name="Carol Client",
            role=UserRole.client_hiring_manager,
            client_id=str(client.id),
            is_active=True
        )
        await hiring_mgr.insert()

        # 2. Login recruiter
        rec_login = await ac.post("/auth/login", json={"email": "recruiter@staffing.com", "password": "recruiter123"})
        assert rec_login.status_code == 200
        rec_token = rec_login.json()["access_token"]
        rec_headers = {"Authorization": f"Bearer {rec_token}"}

        # 3. Create requisition
        req_res = await ac.post("/requisitions", headers=rec_headers, json={
            "title": "Backend Python Engineer",
            "client_id": str(client.id),
            "jd_text": "Requirements: 4+ years experience in Python and FastAPI. Notice period: 30 days."
        })
        assert req_res.status_code == 201
        req_data = req_res.json()
        req_id = req_data["id"]
        assert len(req_data["scorecard"]) > 0

        # 4. Upload candidate CV
        cv_content = b"John Candidate\nEmail: john.cand@example.com\nPhone: 9811223344\nTotal Experience: 5 years\nNotice: 15 days\nTechnical Skills: Python, FastAPI\nDeveloped cloud APIs."
        files = [("files", ("resume.pdf", cv_content, "application/pdf"))]
        upload_res = await ac.post(
            "/candidates/upload",
            headers=rec_headers,
            data={"requisition_id": req_id},
            files=files
        )
        assert upload_res.status_code == 200
        upload_data = upload_res.json()
        assert upload_data["successful"] == 1
        cand_id = upload_data["results"][0]["candidate_id"]
        sub_id = upload_data["results"][0]["submission_id"]

        # 5. Check duplicate upload
        dup_res = await ac.post(
            "/candidates/upload",
            headers=rec_headers,
            data={"requisition_id": req_id},
            files=files
        )
        assert dup_res.status_code == 200
        assert dup_res.json()["duplicate"] == 1

        # 6. Recruiter view candidate profile (records audit log & recruiter_viewed)
        view_res = await ac.get(f"/candidates/{cand_id}?requisition_id={req_id}", headers=rec_headers)
        assert view_res.status_code == 200
        assert view_res.json()["full_name"] == "John Candidate"

        # Check audit log
        audit_res = await ac.get(f"/candidates/{cand_id}/audit-logs", headers=rec_headers)
        assert audit_res.status_code == 200
        assert len(audit_res.json()) >= 1
        assert audit_res.json()[0]["action"] == "viewed"

        # 7. Recruiter submits to client
        sub_client_res = await ac.post(f"/submissions/{sub_id}/submit-to-client", headers=rec_headers)
        assert sub_client_res.status_code == 200
        assert sub_client_res.json()["pipeline_stage"] == PipelineStage.client_reviewed.value

        # 8. Client login & portal checks
        client_login = await ac.post("/auth/login", json={"email": "client@acme.com", "password": "client123"})
        assert client_login.status_code == 200
        client_token = client_login.json()["access_token"]
        client_headers = {"Authorization": f"Bearer {client_token}"}

        # Client list requisitions
        client_reqs = await ac.get("/client/requisitions", headers=client_headers)
        assert client_reqs.status_code == 200
        assert len(client_reqs.json()) == 1

        # Client view submissions (contact info must be masked!)
        client_subs = await ac.get(f"/client/requisitions/{req_id}/submissions", headers=client_headers)
        assert client_subs.status_code == 200
        sub_item = client_subs.json()[0]
        assert sub_item["candidate"]["email"] is None
        assert sub_item["candidate"]["phone"] is None

        # 9. Client proposes interview
        decision_res = await ac.patch(
            f"/client/submissions/{sub_id}/decision",
            headers=client_headers,
            json={
                "decision": ClientDecision.interview_proposed.value,
                "interview_slot": "2026-11-10T14:00:00Z"
            }
        )
        assert decision_res.status_code == 200
        assert decision_res.json()["pipeline_stage"] == PipelineStage.interview.value

        # After stage=interview, client can see contact info!
        client_subs_after = await ac.get(f"/client/requisitions/{req_id}/submissions", headers=client_headers)
        assert client_subs_after.status_code == 200
        assert client_subs_after.json()[0]["candidate"]["email"] == "john.cand@example.com"

        # 10. Pipeline summary
        pipe_res = await ac.get(f"/requisitions/{req_id}/pipeline", headers=rec_headers)
        assert pipe_res.status_code == 200
        assert pipe_res.json()["stages"]["interview"] == 1
