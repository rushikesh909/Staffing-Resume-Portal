#!/usr/bin/env python3
"""
Seed script - populates the DB with realistic demo data.
Re-runnable: clears existing data first (idempotent).
Run from: backend/ directory
Usage: python scripts/seed.py
"""
import asyncio
import hashlib
import sys
import os
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models import (
    User, Client, Requisition, Candidate, Submission, AuditLog,
    ConsentRecord, UserRole, PipelineStage, ClientDecision
)
from app.auth import hash_password
from app.ai.jd_extractor import extract_scorecard_from_jd
from app.ai.cv_parser import extract_profile_and_blind_text
from app.ai.scorer import score_candidate
from app.config import settings


async def main():
    print(f"Connecting to MongoDB at {settings.mongodb_url} (db: {settings.mongodb_db})...")
    client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=client[settings.mongodb_db],
        document_models=[User, Client, Requisition, Candidate, Submission, AuditLog]
    )

    print("Clearing existing data...")
    await User.get_motor_collection().drop()
    await Client.get_motor_collection().drop()
    await Requisition.get_motor_collection().drop()
    await Candidate.get_motor_collection().drop()
    await Submission.get_motor_collection().drop()
    await AuditLog.get_motor_collection().drop()

    print("\n1. Creating clients...")
    techcorp = Client(name="TechCorp Solutions", contact_email="hr@techcorp.in")
    await techcorp.insert()

    finserv = Client(name="FinServ India", contact_email="hr@finserv.in")
    await finserv.insert()
    print(f"  Created Client: {techcorp.name} (id: {techcorp.id})")
    print(f"  Created Client: {finserv.name} (id: {finserv.id})")

    print("\n2. Creating users...")
    users_data = [
        # Recruiters
        {"email": "recruiter@talentbridge.in", "password": "Recruiter@123", "full_name": "Priya Sharma", "role": UserRole.recruiter, "client_id": None},
        {"email": "senior.recruiter@talentbridge.in", "password": "Recruiter@123", "full_name": "Rahul Verma", "role": UserRole.recruiter, "client_id": None},
        # Client Hiring Managers
        {"email": "hiring@techcorp.in", "password": "Client@123", "full_name": "Ankit Gupta", "role": UserRole.client_hiring_manager, "client_id": str(techcorp.id)},
        {"email": "hiring@finserv.in", "password": "Client@123", "full_name": "Deepa Menon", "role": UserRole.client_hiring_manager, "client_id": str(finserv.id)},
        # Delivery Head
        {"email": "head@talentbridge.in", "password": "DeliveryHead@123", "full_name": "Suresh Nair", "role": UserRole.delivery_head, "client_id": None},
    ]

    created_users = {}
    for u in users_data:
        user = User(
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            full_name=u["full_name"],
            role=u["role"],
            client_id=u["client_id"],
            is_active=True,
            created_at=datetime.utcnow()
        )
        await user.insert()
        created_users[u["email"]] = user
        print(f"  Created User: {user.full_name} ({user.email}) - {user.role.value}")

    priya = created_users["recruiter@talentbridge.in"]
    rahul = created_users["senior.recruiter@talentbridge.in"]

    print("\n3. Creating requisitions with AI-extracted scorecards...")
    
    # Requisition 1: Senior Java Developer (TechCorp)
    req1_jd = """
Job Title: Senior Java Developer
Company: TechCorp Solutions
Location: Noida location

About the Role:
We are seeking an experienced Senior Java Developer to lead backend engineering for our enterprise cloud platform. The ideal candidate will design, build, and maintain high-performance microservices and REST APIs handling millions of daily transactions.

Requirements & Qualifications:
- 5-8 years of experience in Java development and architecture
- Deep hands-on expertise with Spring Boot and Spring framework
- Solid architecture background building resilient microservices and distributed systems
- Proven proficiency designing and securing REST APIs
- Experience with Docker containers and CI/CD pipelines
- Strong understanding of relational databases like PostgreSQL and caching with Redis or Kafka
- Candidate must have notice period up to 60 days
- Budget / CTC 18-25 LPA depending on experience and evaluation
"""
    req1_scorecard = extract_scorecard_from_jd(req1_jd)
    req1 = Requisition(
        title="Senior Java Developer",
        client_id=str(techcorp.id),
        jd_text=req1_jd.strip(),
        scorecard=req1_scorecard,
        status="open",
        created_by=str(priya.id),
        created_at=datetime.utcnow() - timedelta(days=14),
        updated_at=datetime.utcnow() - timedelta(days=14)
    )
    await req1.insert()
    print(f"  Created Req 1: {req1.title} with {len(req1.scorecard)} scorecard criteria")

    # Requisition 2: KYC/AML Analyst (FinServ)
    req2_jd = """
Job Title: KYC/AML Analyst
Company: FinServ India
Location: Mumbai location

About the Role:
FinServ India is expanding its Risk & Financial Crime Compliance operations. We require an analytical and meticulous KYC/AML Analyst to conduct customer due diligence, investigate suspicious activities, and maintain statutory compliance with regulatory mandates.

Requirements:
- 3-5 years KYC/AML experience within scheduled commercial banks or regulated NBFCs
- Solid knowledge of banking compliance, RBI guidelines, and PMLA regulatory reporting
- Advanced working knowledge of Excel (VLOOKUP, pivot tables, macros) and data analysis
- Proven track record in transaction monitoring, screening, and STR/SAR filings
- Excellent attention to detail and fraud pattern identification
- Availability with notice period up to 30 days
- Compensation budget / CTC 8-14 LPA based on credentials
"""
    req2_scorecard = extract_scorecard_from_jd(req2_jd)
    req2 = Requisition(
        title="KYC/AML Analyst",
        client_id=str(finserv.id),
        jd_text=req2_jd.strip(),
        scorecard=req2_scorecard,
        status="open",
        created_by=str(priya.id),
        created_at=datetime.utcnow() - timedelta(days=10),
        updated_at=datetime.utcnow() - timedelta(days=10)
    )
    await req2.insert()
    print(f"  Created Req 2: {req2.title} with {len(req2.scorecard)} scorecard criteria")

    # Requisition 3: Full Stack Developer (TechCorp)
    req3_jd = """
Job Title: Full Stack Developer
Company: TechCorp Solutions
Location: Bangalore / Hybrid

About the Role:
TechCorp is building our next-generation customer analytics platform. We are hiring a versatile Full Stack Developer capable of delivering modern, responsive frontend interfaces and high-throughput backend services.

Requirements:
- 3-6 years of professional full stack software engineering experience
- Hands-on mastery of modern React.js and state management
- Proficient in Node.js server-side development and asynchronous programming
- Strong experience with MongoDB document database design and optimization
- Expertise in building and documenting REST APIs
- Hands-on experience with Docker containerization and cloud environments
- Notice up to 45 days preferred
- Target CTC 12-20 LPA
"""
    req3_scorecard = extract_scorecard_from_jd(req3_jd)
    req3 = Requisition(
        title="Full Stack Developer",
        client_id=str(techcorp.id),
        jd_text=req3_jd.strip(),
        scorecard=req3_scorecard,
        status="open",
        created_by=str(rahul.id),
        created_at=datetime.utcnow() - timedelta(days=7),
        updated_at=datetime.utcnow() - timedelta(days=7)
    )
    await req3.insert()
    print(f"  Created Req 3: {req3.title} with {len(req3.scorecard)} scorecard criteria")

    print("\n4. Creating candidates and generating AI scores...")

    candidates_specs = [
        # ==================== JAVA DEVELOPER CANDIDATES (12 for Req 1) ====================
        {
            "full_name": "Vikram Singh",
            "email": "vikram.singh@techmail.in",
            "phone": "+91 9820112233",
            "current_role": "Senior Java Backend Engineer",
            "experience_years": 7.0,
            "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "Docker", "REST API", "PostgreSQL"],
            "notice_days": 30,
            "req": req1,
            "stage": PipelineStage.offer,
            "client_decision": ClientDecision.shortlisted,
            "recruiter_viewed": True,
            "cv_text": """Vikram Singh
Email: vikram.singh@techmail.in | Phone: +91 9820112233 | Location: Noida, India
LinkedIn: linkedin.com/in/vikram-singh-dev

PROFESSIONAL SUMMARY:
Senior Java Backend Engineer with 7 years of experience in Java development and architecture. Specialist in building high-scale Spring Boot microservices, Kafka event streaming architectures, and containerized deployments using Docker and Kubernetes. Currently earning CTC 22 LPA. Notice period is 30 days.

TECHNICAL SKILLS:
- Core Languages & Frameworks: Java 17, Spring Boot, Spring Cloud, Hibernate, JPA
- Architecture & Services: Microservices, REST APIs, GraphQL, Event-Driven Architecture
- Messaging & Caching: Apache Kafka, RabbitMQ, Redis Cache
- Containers & Cloud: Docker, Kubernetes, AWS (ECS, S3, RDS), Jenkins CI/CD
- Databases: PostgreSQL, MongoDB, MySQL

PROFESSIONAL EXPERIENCE:
Lead Software Engineer | Apex Infotech, Noida | Oct 2020 - Present
- Architected enterprise financial microservices using Java and Spring Boot serving 15M requests daily.
- Implemented asynchronous event streaming with Kafka for distributed order processing pipelines.
- Standardized REST APIs across 8 microservice modules with OpenAPI and OAuth2 authentication.
- Spearheaded Docker containerization and orchestrated zero-downtime blue-green deployments on AWS.

Senior Software Engineer | Cognizant, Gurgaon | Jul 2017 - Sep 2020
- Built resilient backend services using Java and Spring Boot for European banking clients.
- Optimized PostgreSQL queries and Redis caching, cutting average API response latency by 45%.
- Authored automated unit testing suites with JUnit and Mockito achieving 88% test coverage.

EDUCATION:
B.Tech in Computer Science & Engineering, IIT BHU (2017)
"""
        },
        {
            "full_name": "Kavya Reddy",
            "email": "kavya.reddy@coderzone.in",
            "phone": "+91 9840223344",
            "current_role": "Java Microservices Specialist",
            "experience_years": 6.0,
            "skills": ["Java", "Spring Boot", "Microservices", "Redis", "REST API", "Docker"],
            "notice_days": 30,
            "req": req1,
            "stage": PipelineStage.interview,
            "client_decision": ClientDecision.interview_proposed,
            "interview_slot": datetime.utcnow() + timedelta(days=2, hours=4),
            "recruiter_viewed": True,
            "cv_text": """Kavya Reddy
Email: kavya.reddy@coderzone.in | Phone: +91 9840223344 | Location: Noida / Remote

SUMMARY:
Results-driven software engineer with 6 years of experience in Java and Spring Boot ecosystems. Proven expertise delivering fault-tolerant microservices, low-latency REST APIs, and distributed caching solutions with Redis. Target compensation CTC 20 LPA. Available on 30 days notice.

CORE COMPETENCIES:
Java, Spring Boot, Microservices, REST APIs, Redis, Docker, Git, Maven, Agile Scrum

WORK HISTORY:
Senior Java Developer | GlobalLogic, Noida | Mar 2021 - Present
- Designed and maintained 12 core microservices using Java and Spring Boot for logistics tracking platform.
- Integrated Redis caching layers to reduce database load by 60% during peak transaction hours.
- Developed secure REST APIs conforming to OpenAPI specifications with comprehensive unit testing.
- Deployed applications via Docker containers onto Kubernetes clusters.

Software Engineer | Wipro Technologies, Hyderabad | Jul 2018 - Feb 2021
- Developed REST APIs and batch jobs using Java and Spring framework.
- Maintained PostgreSQL schemas and implemented database migration scripts with Flyway.

EDUCATION:
B.E. in Information Technology, Osmania University (2018)
"""
        },
        {
            "full_name": "Ritika Bansal",
            "email": "ritika.bansal@devworld.in",
            "phone": "+91 9811334455",
            "current_role": "Senior Backend Developer",
            "experience_years": 6.5,
            "skills": ["Java", "Spring Boot", "Microservices", "REST API", "PostgreSQL"],
            "notice_days": 60,
            "req": req1,
            "stage": PipelineStage.client_reviewed,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": True,
            "cv_text": """Ritika Bansal
Email: ritika.bansal@devworld.in | Phone: +91 9811334455 | Location: Noida, India

CAREER PROFILE:
Senior Backend Developer with 6.5 years of experience in Java software development. Specialized in Spring Boot microservices architectures and REST APIs for retail commerce platforms. Expected CTC 21 LPA. Notice period up to 60 days.

CORE SKILLS:
Java, Spring Boot, Microservices, REST APIs, Hibernate, PostgreSQL, Docker, Git, JUnit

PROFESSIONAL EXPERIENCE:
Senior Software Engineer | PayTM Payments Bank, Noida | Jan 2021 - Present
- Built scalable merchant payment gateway microservices using Java and Spring Boot.
- Engineered high-throughput REST APIs handling 8,000 requests per second at peak.
- Maintained Docker build pipelines and managed production release cycles on Linux servers.
- Mentored junior engineers and conducted code reviews adhering to Clean Code standards.

Software Developer | Infosys Ltd, Chandigarh | Jul 2017 - Dec 2020
- Developed web services using Java and Spring framework for enterprise retail banking clients.
- Automated data integration workflows and integrated PostgreSQL databases.

ACADEMICS:
B.Tech in Computer Science, Punjab Engineering College (2017)
"""
        },
        {
            "full_name": "Ananya Krishnamurthy",
            "email": "ananya.k@cloudtech.in",
            "phone": "+91 9870445566",
            "current_role": "Staff Java Engineer",
            "experience_years": 5.0,
            "skills": ["Java", "Spring Boot", "Microservices", "AWS", "REST API", "Docker"],
            "notice_days": 45,
            "req": req1,
            "stage": PipelineStage.client_reviewed,
            "client_decision": ClientDecision.shortlisted,
            "recruiter_viewed": True,
            "cv_text": """Ananya Krishnamurthy
Email: ananya.k@cloudtech.in | Phone: +91 9870445566 | Location: Delhi NCR

PROFESSIONAL SUMMARY:
Backend Software Engineer with 5 years of experience in Java development and cloud infrastructure. Strong track record of designing distributed microservices with Spring Boot and AWS cloud primitives. Current compensation CTC 19 LPA. Available to join within 45 days notice.

TECHNICAL SKILLS:
Java, Spring Boot, Spring Cloud, AWS, Microservices, REST APIs, Docker, MySQL, Redis

EXPERIENCE:
Senior Java Developer | MakeMyTrip, Gurgaon | Aug 2021 - Present
- Engineered flight booking search services utilizing Java and Spring Boot microservices.
- Deployed microservices on AWS ECS using Docker containers and CloudWatch monitoring.
- Designed REST APIs with JSON schemas, resilient circuit breakers, and rate limiters.

Software Engineer | TCS, Noida | Jun 2019 - Jul 2021
- Created backend microservices using Spring Boot and relational databases.
- Participated in agile sprints, code reviews, and defect prevention audits.

EDUCATION:
B.Tech in IT, Delhi Technological University (2019)
"""
        },
        {
            "full_name": "Rohit Joshi",
            "email": "rohit.joshi@techpulse.in",
            "phone": "+91 9819556677",
            "current_role": "Lead Java Developer",
            "experience_years": 8.0,
            "skills": ["Java", "Spring", "Spring Boot", "Redis", "REST API"],
            "notice_days": 60,
            "req": req1,
            "stage": PipelineStage.shortlisted,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": True,
            "cv_text": """Rohit Joshi
Email: rohit.joshi@techpulse.in | Phone: +91 9819556677 | Location: Noida, India

EXECUTIVE OVERVIEW:
Seasoned software engineer with 8 years of experience in Java enterprise applications. Expert in Spring framework, Spring Boot, JPA, and Redis caching architectures. Target CTC 24 LPA. Official notice period 60 days.

TECHNICAL TOOLKIT:
Java, Spring Boot, Spring, Microservices, REST APIs, JPA, Redis, Oracle DB, Git

WORK EXPERIENCE:
Lead Developer | Tech Mahindra, Noida | May 2020 - Present
- Led engineering squad of 7 developers building telecom billing platforms with Java and Spring Boot.
- Implemented Redis distributed caching and connection pooling to accelerate transaction throughput.
- Authored production-ready REST APIs integrated with external billing vendor gateways.

Senior Developer | HCL Technologies, Noida | Jul 2016 - Apr 2020
- Developed enterprise Java applications with Spring MVC and Hibernate ORM.
- Managed relational database tuning and resolved critical performance bottlenecks.

EDUCATION:
M.Sc. in Computer Science, University of Delhi (2016)
"""
        },
        {
            "full_name": "Sanjay Kulkarni",
            "email": "sanjay.kulkarni@infradev.in",
            "phone": "+91 9822667788",
            "current_role": "Backend Java Engineer",
            "experience_years": 6.0,
            "skills": ["Java", "Spring Boot", "PostgreSQL", "Docker", "REST API"],
            "notice_days": 60,
            "req": req1,
            "stage": PipelineStage.shortlisted,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Sanjay Kulkarni
Email: sanjay.kulkarni@infradev.in | Phone: +91 9822667788 | Location: Pune / Noida (willing to relocate)

SUMMARY:
Software Engineer with 6 years of experience in Java enterprise solutions. Proficient in Spring Boot, PostgreSQL database optimizations, Docker workflows, and REST APIs. Current package CTC 18.5 LPA. Notice period 60 days.

SKILLS:
Java, Spring Boot, PostgreSQL, Docker, REST APIs, Linux, Jenkins, Maven

EXPERIENCE:
Senior Software Engineer | Persistent Systems | Jan 2021 - Present
- Engineered high-reliability backend services with Java and Spring Boot.
- Standardized REST APIs for IoT device management systems.
- Containerized applications using Docker and configured continuous testing pipelines.

Software Engineer | Cybage Software | Jul 2018 - Dec 2020
- Built backend business logic in Java and maintained relational databases.

EDUCATION:
B.E. in Computer Engineering, Pune University (2018)
"""
        },
        {
            "full_name": "Deepak Yadav",
            "email": "deepak.yadav@cloudpro.in",
            "phone": "+91 9810778899",
            "current_role": "DevOps & Java Engineer",
            "experience_years": 5.5,
            "skills": ["Java", "Spring Boot", "Kubernetes", "Docker", "REST API"],
            "notice_days": 45,
            "req": req1,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Deepak Yadav
Email: deepak.yadav@cloudpro.in | Phone: +91 9810778899 | Location: Greater Noida

SUMMARY:
Backend Engineer with 5.5 years of experience in Java systems programming, Spring Boot microservices, and Docker container orchestration. Expected CTC 19 LPA. Notice period 45 days.

SKILLS:
Java, Spring Boot, Docker, Kubernetes, CI/CD, REST APIs, Git, PostgreSQL

EXPERIENCE:
Software Engineer | Genpact, Noida | Aug 2020 - Present
- Developed microservices in Java and Spring Boot supporting insurance claim adjudication.
- Created robust REST APIs and streamlined deployment with Docker and Kubernetes.

Associate Engineer | Mindtree | Jul 2018 - Jul 2020
- Maintained Java web applications and wrote automated unit tests.

EDUCATION:
B.Tech in Computer Science, AKTU (2018)
"""
        },
        {
            "full_name": "Amit Sharma",
            "email": "amit.sharma@enterprisejava.in",
            "phone": "+91 9818889900",
            "current_role": "Senior Java Architect",
            "experience_years": 7.5,
            "skills": ["Java", "Spring Boot", "Microservices", "Kafka", "REST API"],
            "notice_days": 90,
            "req": req1,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Amit Sharma
Email: amit.sharma@enterprisejava.in | Phone: +91 9818889900 | Location: Delhi NCR

PROFILE:
Architectural developer with 7.5 years of experience in Java enterprise software. Extensive experience developing Spring Boot microservices and Kafka event streaming platforms. Current CTC 23 LPA. Official contractual notice period 90 days.

SKILLS:
Java, Spring Boot, Microservices, Kafka, REST APIs, Oracle, Spring Cloud

EXPERIENCE:
Senior Consultant | Capgemini, Noida | Nov 2019 - Present
- Designed microservices architecture using Java and Spring Boot for automotive client.
- Orchestrated Kafka distributed streaming queues. Note: Notice period is 90 days as per company policy.

Software Engineer | LTI | Jun 2016 - Oct 2019
- Developed Java REST APIs and enterprise persistence modules.

EDUCATION:
B.Tech in CS, Jaypee Institute of Information Technology (2016)
"""
        },
        {
            "full_name": "Pooja Nair",
            "email": "pooja.nair@itpro.in",
            "phone": "+91 9821990011",
            "current_role": "Java Developer",
            "experience_years": 4.0,
            "skills": ["Java", "Hibernate", "REST API"],
            "notice_days": 90,
            "req": req1,
            "stage": PipelineStage.sourced,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Pooja Nair
Email: pooja.nair@itpro.in | Phone: +91 9821990011 | Location: Noida, India

CAREER OBJECTIVE:
Motivated developer with 4 years of experience in Java software development. Experienced in building web services with Hibernate and REST APIs. Notice period 90 days. Expected CTC 14 LPA.

SKILLS:
Java, Hibernate, REST APIs, MySQL, Eclipse, Git

EXPERIENCE:
Software Engineer | Birlasoft, Noida | Jul 2020 - Present
- Implemented business logic modules using Java and Hibernate ORM.
- Developed basic REST APIs for external vendor integrations.

EDUCATION:
B.E. in IT, Mumbai University (2020)
"""
        },
        {
            "full_name": "Meera Pillai",
            "email": "meera.pillai@juniorcode.in",
            "phone": "+91 9890113355",
            "current_role": "Junior Java Developer",
            "experience_years": 2.0,
            "skills": ["Java", "REST API"],
            "notice_days": 15,
            "req": req1,
            "stage": PipelineStage.sourced,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Meera Pillai
Email: meera.pillai@juniorcode.in | Phone: +91 9890113355 | Location: Delhi NCR

PROFILE:
Enthusiastic junior programmer with 2 years of experience in Java web development. Capable of building clean REST APIs and writing unit test cases. Immediate joiner with notice period 15 days. Current CTC 6 LPA.

SKILLS:
Java, REST APIs, Core Java, HTML, CSS, SQL, Git

EXPERIENCE:
Junior Developer | TechSpire Solutions | Aug 2022 - Present
- Wrote Java utility functions and maintained REST API endpoints.
- Resolved minor bugs and drafted test cases.

EDUCATION:
BCA, Amity University (2022)
"""
        },
        {
            "full_name": "Arjun Rawat",
            "email": "arjun.rawat@finrisk.in",
            "phone": "+91 9871224466",
            "current_role": "AML & KYC Specialist",
            "experience_years": 3.0,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 30,
            "req": req1,
            "stage": PipelineStage.sourced,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Arjun Rawat
Email: arjun.rawat@finrisk.in | Phone: +91 9871224466 | Location: Delhi NCR

PROFESSIONAL SUMMARY:
Banking compliance professional with 3 years of experience in KYC, AML, customer due diligence, and Excel reporting. Strong background in regulatory reporting and risk mitigation. Available with notice period 30 days. CTC 9 LPA.

SKILLS:
KYC, AML, Excel, Banking Compliance, Fraud Investigation, Regulatory Reporting

EXPERIENCE:
KYC Associate | Axis Bank | Sep 2021 - Present
- Conducted customer identification procedures and verified PEP and sanctions lists.
- Utilized Excel pivot tables to prepare statutory compliance filings.

EDUCATION:
B.Com, Delhi University (2021)
"""
        },
        {
            "full_name": "Ritu Agarwal",
            "email": "ritu.agarwal@pythondjango.in",
            "phone": "+91 9811446688",
            "current_role": "Python Backend Engineer",
            "experience_years": 3.5,
            "skills": ["Python", "Django", "PostgreSQL"],
            "notice_days": 30,
            "req": req1,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Ritu Agarwal
Email: ritu.agarwal@pythondjango.in | Phone: +91 9811446688 | Location: Noida

PROFILE:
Backend web programmer with 3.5 years of experience in Python and Django framework development. Adept at building database queries with PostgreSQL and managing REST APIs. Notice period 30 days. Current CTC 12 LPA.

SKILLS:
Python, Django, Flask, PostgreSQL, Docker, Linux, Git

EXPERIENCE:
Python Developer | AppSquadz, Noida | Dec 2020 - Present
- Built web portals and backend services using Python and Django.
- Managed database schemas in PostgreSQL.

EDUCATION:
B.Tech in IT, IP University (2020)
"""
        },

        # ==================== KYC / AML ANALYST CANDIDATES (8 for Req 2) ====================
        {
            "full_name": "Nisha Desai",
            "email": "nisha.desai@compliancepro.in",
            "phone": "+91 9820557799",
            "current_role": "Senior AML Analyst",
            "experience_years": 3.5,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 15,
            "req": req2,
            "stage": PipelineStage.joined,
            "client_decision": ClientDecision.shortlisted,
            "recruiter_viewed": True,
            "cv_text": """Nisha Desai
Email: nisha.desai@compliancepro.in | Phone: +91 9820557799 | Location: Mumbai

PROFESSIONAL SUMMARY:
Dedicated compliance specialist with 3.5 years of experience in KYC, AML, regulatory reporting, and risk analysis. Extensive experience in banking compliance, transaction monitoring, and advanced Excel modeling. Notice period 15 days. Expected CTC 11 LPA.

TECHNICAL & DOMAIN SKILLS:
KYC, AML, Excel (VLOOKUP, Pivot, Macros), Banking Compliance, Regulatory Reporting, PMLA, Sanctions Screening, Risk Analysis

EXPERIENCE:
AML Compliance Analyst | HDFC Bank, Mumbai | Feb 2021 - Present
- Conducted end-to-end KYC reviews and transaction monitoring for high-risk corporate client accounts.
- Automated quarterly regulatory reporting submissions using advanced Excel macros, saving 20 hours per cycle.
- Maintained rigorous compliance with RBI and banking compliance guidelines, identifying 14 critical AML anomalies.

Compliance Officer | ICICI Securities | Jun 2019 - Jan 2021
- Performed customer due diligence, verified CKYC records, and handled PEP sanctions checks.

EDUCATION:
MBA in Banking & Finance, Narsee Monjee Institute of Management Studies (2019)
"""
        },
        {
            "full_name": "Suresh Patel",
            "email": "suresh.patel@bankingaudit.in",
            "phone": "+91 9821668800",
            "current_role": "KYC Compliance Specialist",
            "experience_years": 4.0,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 30,
            "req": req2,
            "stage": PipelineStage.interview,
            "client_decision": ClientDecision.interview_proposed,
            "interview_slot": datetime.utcnow() + timedelta(days=3, hours=2),
            "recruiter_viewed": True,
            "cv_text": """Suresh Patel
Email: suresh.patel@bankingaudit.in | Phone: +91 9821668800 | Location: Mumbai

EXECUTIVE PROFILE:
Banking operations expert with 4 years of experience in KYC customer onboarding, AML transaction surveillance, and regulatory reporting. Skilled in banking compliance and Excel analysis. Notice period 30 days. Current CTC 12 LPA.

CORE SKILLS:
KYC, AML, Excel, Banking Compliance, CKYC, Regulatory Reporting, Fraud Detection

EXPERIENCE:
Senior KYC Analyst | Kotak Mahindra Bank, Mumbai | Jan 2020 - Present
- Spearheaded KYC remediation and institutional due diligence in compliance with RBI standards.
- Designed Excel tracking dashboards for transaction monitoring and suspicious activity investigations.
- Ensured 100% adherence to regulatory reporting timeframes for SAR escalations.

KYC Associate | Yes Bank | Jul 2018 - Dec 2019
- Verified individual and entity customer documents against CKYC registry.

EDUCATION:
B.Com, Mumbai University (2018)
"""
        },
        {
            "full_name": "Mohammed Farhan",
            "email": "farhan.aml@auditdesk.in",
            "phone": "+91 9833779911",
            "current_role": "AML Transaction Monitoring Specialist",
            "experience_years": 5.0,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 45,
            "req": req2,
            "stage": PipelineStage.client_reviewed,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": True,
            "cv_text": """Mohammed Farhan
Email: farhan.aml@auditdesk.in | Phone: +91 9833779911 | Location: Mumbai

SUMMARY:
Financial crime investigator with 5 years of experience in AML transaction monitoring and KYC validations. Well-versed in SWIFT message scrutiny, banking compliance, and Excel analytics. Notice period 45 days. CTC 13.5 LPA.

SKILLS:
AML, KYC, Excel, Banking Compliance, SWIFT, Regulatory Reporting, PMLA

EXPERIENCE:
AML Investigator | Standard Chartered Global Business Services | Oct 2019 - Present
- Monitored cross-border wire transfers and investigated suspicious alerts for AML compliance.
- Authored detailed investigation summaries and prepared regulatory reporting data in Excel.

Compliance Analyst | State Bank of India | Jun 2017 - Sep 2019
- Conducted customer due diligence and renewed periodic KYC profiles.

EDUCATION:
B.Sc. Mathematics, University of Mumbai (2017)
"""
        },
        {
            "full_name": "Pradeep Nambiar",
            "email": "pradeep.nambiar@finservices.in",
            "phone": "+91 9845880022",
            "current_role": "Operations Compliance Analyst",
            "experience_years": 4.0,
            "skills": ["KYC", "AML", "Compliance", "Excel"],
            "notice_days": 60,
            "req": req2,
            "stage": PipelineStage.shortlisted,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": True,
            "cv_text": """Pradeep Nambiar
Email: pradeep.nambiar@finservices.in | Phone: +91 9845880022 | Location: Mumbai

CAREER SUMMARY:
Banking operations and compliance professional with 4 years of experience in retail banking compliance and KYC audits. Proficient in regulatory reporting and Excel spreadsheets. Notice period 60 days. CTC 10 LPA.

SKILLS:
Banking Compliance, KYC, AML, Excel, Regulatory Reporting, Risk Control

EXPERIENCE:
Operations Executive | IDFC First Bank | Sep 2020 - Present
- Handled branch-level KYC onboarding compliance and audited documentation for new accounts.
- Prepared weekly risk summaries using Excel for the regional compliance committee.

EDUCATION:
B.Com, Pune University (2020)
"""
        },
        {
            "full_name": "Rajesh Kadam",
            "email": "rajesh.kadam@amlguard.in",
            "phone": "+91 9867991133",
            "current_role": "Compliance Analyst",
            "experience_years": 4.5,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 30,
            "req": req2,
            "stage": PipelineStage.shortlisted,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Rajesh Kadam
Email: rajesh.kadam@amlguard.in | Phone: +91 9867991133 | Location: Mumbai / Navi Mumbai

SUMMARY:
Compliance professional with 4.5 years of experience in KYC identification and AML investigations. Familiar with regulatory reporting, banking compliance standards, and Excel analytics. Notice period 30 days. CTC 11.5 LPA.

SKILLS:
KYC, AML, Excel, Banking Compliance, Sanctions Screening, Regulatory Reporting

EXPERIENCE:
Compliance Officer | RBL Bank | Dec 2019 - Present
- Screened high-net-worth clients against international watchlists and conducted enhanced due diligence.
- Compiled statutory regulatory reporting files using Excel functions.

EDUCATION:
M.Com, Mumbai University (2019)
"""
        },
        {
            "full_name": "Aarti Chandra",
            "email": "aarti.chandra@risktrack.in",
            "phone": "+91 9811002244",
            "current_role": "KYC Compliance Officer",
            "experience_years": 3.0,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 30,
            "req": req2,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Aarti Chandra
Email: aarti.chandra@risktrack.in | Phone: +91 9811002244 | Location: Mumbai

PROFILE:
Customer due diligence and compliance officer with 3 years of experience in retail banking compliance and KYC remediation. Proficient in Excel and regulatory reporting routines. Notice period 30 days. CTC 9 LPA.

SKILLS:
KYC, AML, Excel, Banking Compliance, Regulatory Reporting, Document Verification

EXPERIENCE:
KYC Analyst | IndusInd Bank | Aug 2021 - Present
- Verified individual identity records and supported banking compliance teams with regular audits.

EDUCATION:
BBA, NMIMS Mumbai (2021)
"""
        },
        {
            "full_name": "Neha Kulkarni",
            "email": "neha.kulkarni@finaudit.in",
            "phone": "+91 9833113355",
            "current_role": "Junior AML Analyst",
            "experience_years": 3.0,
            "skills": ["KYC", "AML", "Excel", "Compliance"],
            "notice_days": 15,
            "req": req2,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Neha Kulkarni
Email: neha.kulkarni@finaudit.in | Phone: +91 9833113355 | Location: Mumbai

SUMMARY:
Financial crime risk associate with 3 years of experience in transaction monitoring, KYC validation, and regulatory reporting in commercial banking. Notice period 15 days. CTC 9.5 LPA.

SKILLS:
AML, KYC, Excel, Banking Compliance, Fraud Screening, Regulatory Reporting

EXPERIENCE:
AML Analyst | Barclays Shared Services | Sep 2021 - Present
- Conducted Level 1 alert clearing and transaction monitoring in banking compliance operations.

EDUCATION:
B.Com, Pune University (2021)
"""
        },
        {
            "full_name": "Lakshmi Rao",
            "email": "lakshmi.rao@dataentryfin.in",
            "phone": "+91 9840224466",
            "current_role": "KYC Data Associate",
            "experience_years": 2.5,
            "skills": ["KYC", "Excel"],
            "notice_days": 30,
            "req": req2,
            "stage": PipelineStage.sourced,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Lakshmi Rao
Email: lakshmi.rao@dataentryfin.in | Phone: +91 9840224466 | Location: Mumbai

PROFILE:
Banking associate with 2.5 years of experience in KYC data entry and customer record indexing. Working knowledge of basic Excel spreadsheets. Notice period 30 days. CTC 6 LPA.

SKILLS:
KYC, Excel, Data Entry, Document Archiving, Customer Service

EXPERIENCE:
KYC Assistant | Federal Bank | Jan 2022 - Present
- Scanned identity proofs and updated customer databases.

EDUCATION:
B.Com, Mumbai University (2022)
"""
        },

        # ==================== FULL STACK DEVELOPER CANDIDATES (5 for Req 3) ====================
        {
            "full_name": "Nikhil Mehta",
            "email": "nikhil.mehta@stacklead.in",
            "phone": "+91 9820335577",
            "current_role": "Senior Full Stack Engineer",
            "experience_years": 5.0,
            "skills": ["React.js", "Node.js", "MongoDB", "Docker", "REST API"],
            "notice_days": 30,
            "req": req3,
            "stage": PipelineStage.interview,
            "client_decision": ClientDecision.interview_proposed,
            "interview_slot": datetime.utcnow() + timedelta(days=4, hours=3),
            "recruiter_viewed": True,
            "cv_text": """Nikhil Mehta
Email: nikhil.mehta@stacklead.in | Phone: +91 9820335577 | Location: Bangalore

CAREER OVERVIEW:
Full stack software engineer with 5 years of experience in modern JavaScript web development. Comprehensive mastery of React.js frontends, Node.js microservices, MongoDB database modeling, and Docker deployments. Available with notice period 30 days. Current package CTC 18 LPA.

SKILLS:
React.js, Node.js, MongoDB, Docker, REST APIs, Express, TypeScript, Next.js, Redux, Git

EXPERIENCE:
Senior Full Stack Developer | Swiggy, Bangalore | Jan 2021 - Present
- Architected merchant onboarding dashboard with React.js and TypeScript, increasing conversion by 22%.
- Built high-throughput backend services using Node.js and MongoDB handling 50k concurrent sessions.
- Designed comprehensive REST APIs and packaged applications into lightweight Docker containers.
- Implemented robust MongoDB aggregation pipelines and indexing strategies.

Full Stack Engineer | Zeta Suite | Jul 2019 - Dec 2020
- Developed single-page applications using React.js and backend microservices with Node.js.

EDUCATION:
B.Tech in Computer Science, NIT Karnataka Surathkal (2019)
"""
        },
        {
            "full_name": "Arun Babu",
            "email": "arun.babu@webcraft.in",
            "phone": "+91 9845446688",
            "current_role": "Full Stack Developer",
            "experience_years": 3.0,
            "skills": ["React.js", "Node.js", "MongoDB", "REST API", "Docker"],
            "notice_days": 15,
            "req": req3,
            "stage": PipelineStage.client_reviewed,
            "client_decision": ClientDecision.shortlisted,
            "recruiter_viewed": True,
            "cv_text": """Arun Babu
Email: arun.babu@webcraft.in | Phone: +91 9845446688 | Location: Bangalore

SUMMARY:
Fast-paced web engineer with 3 years of experience in React.js, Node.js, and MongoDB stack development. Experienced in containerizing apps with Docker and creating clean REST APIs. Immediate joiner with notice period 15 days. Expected CTC 14 LPA.

SKILLS:
React.js, Node.js, MongoDB, Docker, REST APIs, JavaScript, Tailwind, Git

EXPERIENCE:
Full Stack Developer | Razorpay, Bangalore | Sep 2021 - Present
- Created developer portal dashboard using React.js and Tailwind CSS.
- Built backend webhooks and REST APIs with Node.js and MongoDB.
- Deployed production workloads inside Docker containers with GitHub Actions CI/CD.

EDUCATION:
B.Tech in CSE, PES University Bangalore (2021)
"""
        },
        {
            "full_name": "Tanvi Deshmukh",
            "email": "tanvi.d@codelabs.in",
            "phone": "+91 9822557799",
            "current_role": "Full Stack Engineer",
            "experience_years": 4.5,
            "skills": ["React.js", "Node.js", "MongoDB", "Docker", "REST API"],
            "notice_days": 30,
            "req": req3,
            "stage": PipelineStage.shortlisted,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": True,
            "cv_text": """Tanvi Deshmukh
Email: tanvi.d@codelabs.in | Phone: +91 9822557799 | Location: Bangalore

PROFILE:
Full stack developer with 4.5 years of experience in building enterprise cloud portals using React.js, Node.js, and MongoDB. Skilled in Docker containerization and REST APIs. Notice period 30 days. CTC 16 LPA.

SKILLS:
React.js, Node.js, MongoDB, Docker, REST APIs, TypeScript, Express, Jest

EXPERIENCE:
Full Stack Engineer | Freshworks, Chennai / Bangalore | Nov 2020 - Present
- Designed customer analytics widgets in React.js and backend query layers in Node.js and MongoDB.
- Documented REST APIs with Swagger and containerized services using Docker.

EDUCATION:
B.E. in Computer Science, Anna University (2020)
"""
        },
        {
            "full_name": "Swati Saxena",
            "email": "swati.saxena@stackengineer.in",
            "phone": "+91 9811668800",
            "current_role": "Backend / Fullstack Developer",
            "experience_years": 4.0,
            "skills": ["React.js", "REST API", "PostgreSQL"],
            "notice_days": 45,
            "req": req3,
            "stage": PipelineStage.screened,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Swati Saxena
Email: swati.saxena@stackengineer.in | Phone: +91 9811668800 | Location: Bangalore

CAREER OVERVIEW:
Software engineer with 4 years of experience building web applications. Proficient in React.js interfaces, Express microservices, and PostgreSQL database queries. Notice period 45 days. CTC 15 LPA.

SKILLS:
React.js, Express, PostgreSQL, REST APIs, JavaScript, Git

EXPERIENCE:
Software Engineer | Postman, Bangalore | Aug 2020 - Present
- Created frontend views using React.js and managed API contracts with REST APIs.
- Maintained PostgreSQL schemas and query optimization.

EDUCATION:
B.Tech in IT, Manipal Institute of Technology (2020)
"""
        },
        {
            "full_name": "Harsh Vardhan",
            "email": "harsh.vardhan@frontenddev.in",
            "phone": "+91 9833880022",
            "current_role": "Junior Frontend Developer",
            "experience_years": 2.0,
            "skills": ["HTML", "CSS", "JavaScript"],
            "notice_days": 15,
            "req": req3,
            "stage": PipelineStage.sourced,
            "client_decision": ClientDecision.pending,
            "recruiter_viewed": False,
            "cv_text": """Harsh Vardhan
Email: harsh.vardhan@frontenddev.in | Phone: +91 9833880022 | Location: Bangalore

PROFILE:
Entry-level frontend web designer with 2 years of experience in HTML, CSS, and basic JavaScript. Passionate about learning full stack development. Immediate availability with 15 days notice. CTC 5.5 LPA.

SKILLS:
HTML, CSS, JavaScript, Bootstrap, jQuery, Git

EXPERIENCE:
Frontend Intern & Junior Developer | PixelCraft Studio | Jun 2022 - Present
- Built static web pages using HTML, CSS, and responsive layout designs.

EDUCATION:
B.Sc. Computer Science, Bangalore University (2022)
"""
        }
    ]

    seeded_candidates_count = 0
    seeded_submissions_count = 0

    for spec in candidates_specs:
        raw_text = spec["cv_text"].strip()
        filename = f"{spec['full_name'].lower().replace(' ', '_')}_cv.pdf"
        
        # Profile & blind text extraction
        profile, blind_text, err = extract_profile_and_blind_text(raw_text, filename)
        
        # Compute exact fingerprint required: sha256(f"{email.lower().strip()}:{phone_digits[-10:]}".encode()).hexdigest()
        phone_digits = "".join(filter(str.isdigit, spec["phone"]))
        fp_source = f"{spec['email'].lower().strip()}:{phone_digits[-10:]}"
        fingerprint = hashlib.sha256(fp_source.encode("utf-8")).hexdigest()

        cand = Candidate(
            full_name=spec["full_name"],
            email=spec["email"],
            phone=spec["phone"],
            current_role=spec["current_role"],
            experience_years=spec["experience_years"],
            skills=spec["skills"],
            notice_days=spec["notice_days"],
            raw_text=raw_text,
            blind_text=blind_text,
            fingerprint=fingerprint,
            consent=ConsentRecord(given=True, timestamp=datetime.utcnow(), purpose="hiring"),
            file_name=filename,
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        await cand.insert()
        seeded_candidates_count += 1

        # Real AI Scoring with score_candidate
        req = spec["req"]
        evidences, score = score_candidate(cand, req.scorecard)

        # Create submission
        sub = Submission(
            requisition_id=str(req.id),
            candidate_id=str(cand.id),
            client_id=req.client_id,
            ai_score=score,
            criteria_scores=evidences,
            pipeline_stage=spec["stage"],
            client_decision=spec.get("client_decision", ClientDecision.pending),
            interview_slot=spec.get("interview_slot"),
            recruiter_viewed=spec["recruiter_viewed"],
            recruiter_viewed_at=datetime.utcnow() - timedelta(days=2) if spec["recruiter_viewed"] else None,
            submitted_at=datetime.utcnow() - timedelta(days=4),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )
        await sub.insert()
        seeded_submissions_count += 1

        # Create AuditLog for viewed candidates
        if spec["recruiter_viewed"]:
            audit = AuditLog(
                candidate_id=str(cand.id),
                viewer_user_id=str(priya.id),
                viewer_role="recruiter",
                requisition_id=str(req.id),
                action="viewed",
                timestamp=datetime.utcnow() - timedelta(days=2)
            )
            await audit.insert()

        print(f"  Candidate #{seeded_candidates_count:02d}: {cand.full_name:22s} | Score: {score:4.1f} | Stage: {sub.pipeline_stage.value:15s} | Req: {req.title}")

    print("\n" + "="*70)
    print("Seed Complete! Summary:")
    print(f"  Clients:      2")
    print(f"  Users:        {len(users_data)}")
    print(f"  Requisitions: 3")
    print(f"  Candidates:   {seeded_candidates_count}")
    print(f"  Submissions:  {seeded_submissions_count}")
    print("="*70)

    print("\nDemo Credentials:")
    print("-" * 75)
    print(f"{'Role':<22} | {'Email':<32} | {'Password'}")
    print("-" * 75)
    for u in users_data:
        print(f"{u['role'].value:<22} | {u['email']:<32} | {u['password']}")
    print("-" * 75)


if __name__ == "__main__":
    asyncio.run(main())
