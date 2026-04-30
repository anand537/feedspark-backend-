#!/usr/bin/env python3
"""
Generate comprehensive seed_data.sql for Auto-Feedback Generator.
"""

import random
from datetime import datetime, timedelta

# Fixed UUIDs for deterministic relationships
ADMINS = [
    ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1", "Sarah Chen", "sarah.chen@afg.edu"),
    ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2", "Marcus Johnson", "marcus.j@afg.edu"),
]

MENTORS = [
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm1", "Dr. Emily Watson", "emily.watson@afg.edu"),
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm2", "Prof. James Miller", "james.miller@afg.edu"),
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm3", "Dr. Aisha Patel", "aisha.patel@afg.edu"),
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm4", "Robert Kim", "robert.kim@afg.edu"),
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm5", "Dr. Lisa Thompson", "lisa.thompson@afg.edu"),
    ("mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm6", "Prof. David Okafor", "david.okafor@afg.edu"),
]

STUDENTS = [
    ("ssssssss-ssss-ssss-ssss-sssssssssss1", "Alex Rivera", "alex.rivera@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss2", "Jordan Blake", "jordan.blake@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss3", "Taylor Morgan", "taylor.morgan@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss4", "Morgan Lee", "morgan.lee@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss5", "Casey Brooks", "casey.brooks@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss6", "Riley Patel", "riley.patel@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss7", "Quinn Foster", "quinn.foster@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss8", "Avery Kim", "avery.kim@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-sssssssssss9", "Parker Nguyen", "parker.nguyen@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss10", "Drew Campbell", "drew.campbell@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss11", "Sam Torres", "sam.torres@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss12", "Jamie Walsh", "jamie.walsh@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss13", "Reese Adams", "reese.adams@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss14", "Kendall Hayes", "kendall.hayes@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss15", "Hayden Price", "hayden.price@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss16", "Bailey Cooper", "bailey.cooper@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss17", "Cameron Diaz", "cameron.diaz@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss18", "Dakota Reed", "dakota.reed@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss19", "Emery Clark", "emery.clark@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss20", "Finley Gray", "finley.gray@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss21", "Harper Bell", "harper.bell@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss22", "Jordan Ellis", "jordan.ellis@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss23", "Kai Sharma", "kai.sharma@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss24", "Logan Woods", "logan.woods@student.afg.edu"),
    ("ssssssss-ssss-ssss-ssss-ssssssssss25", "Morgan Hale", "morgan.hale@student.afg.edu"),
]

COURSES = [
    ("cccccccc-cccc-cccc-cccc-ccccccccccc1", "Full-Stack Web Development Bootcamp", "Master modern web development with React, Node.js, and PostgreSQL. Build real-world projects from scratch.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm1", 16, 1299.00, 4.85, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc2", "Data Science & Machine Learning Fundamentals", "Learn Python, pandas, scikit-learn, and neural networks. Hands-on projects with real datasets.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm2", 20, 1599.00, 4.72, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc3", "UI/UX Design Masterclass", "From wireframes to high-fidelity prototypes. Master Figma, design systems, and user research.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm3", 12, 899.00, 4.90, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc4", "Cloud Computing with AWS", "Deploy scalable applications on AWS. EC2, S3, Lambda, RDS, and CI/CD pipelines.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm4", 14, 1199.00, 4.65, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc5", "Mobile App Development with React Native", "Build cross-platform mobile apps for iOS and Android using React Native and Expo.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm1", 12, 999.00, 4.78, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc6", "DevOps & CI/CD Engineering", "Master Docker, Kubernetes, Jenkins, and GitHub Actions. Automate your deployment pipeline.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm5", 10, 1099.00, 4.55, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc7", "Cybersecurity Fundamentals", "Learn ethical hacking, network security, penetration testing, and security best practices.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm4", 16, 1399.00, 4.60, "active"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc8", "Blockchain & Web3 Development", "Smart contracts with Solidity, DeFi protocols, NFT marketplaces, and dApp development.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm6", 14, 1499.00, 4.45, "completed"),
    ("cccccccc-cccc-cccc-cccc-ccccccccccc9", "Product Management Essentials", "Agile methodologies, user stories, roadmap planning, stakeholder management, and metrics.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm3", 8, 799.00, 4.82, "active"),
    ("cccccccc-cccc-cccc-cccc-cccccccccc10", "Advanced Python Programming", "Deep dive into Python: decorators, generators, async/await, metaclasses, and performance optimization.", "mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmmmmm2", 10, 899.00, 4.70, "active"),
]

ASSIGNMENT_TEMPLATES = {
    "cccccccc-cccc-cccc-cccc-ccccccccccc1": [
        ("Build a REST API with Express", "Create a fully functional REST API with authentication, CRUD operations, and proper error handling.", 100),
        ("React Component Library", "Build a reusable component library with Storybook, including buttons, forms, and data tables.", 100),
        ("Full-Stack E-commerce App", "Develop a complete e-commerce application with shopping cart, checkout, and payment integration.", 150),
        ("Database Design & Optimization", "Design a normalized database schema and write optimized PostgreSQL queries.", 100),
        ("Deploy to Production", "Deploy your full-stack application to AWS/Vercel with CI/CD pipeline.", 100),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc2": [
        ("Data Cleaning & EDA", "Clean a messy dataset and perform exploratory data analysis with visualizations.", 100),
        ("Predictive Model with scikit-learn", "Build a classification or regression model and evaluate with cross-validation.", 150),
        ("Deep Learning Image Classifier", "Train a CNN to classify images using TensorFlow or PyTorch.", 200),
        ("NLP Sentiment Analysis", "Build a sentiment analysis pipeline using transformers and evaluate on test data.", 150),
        ("End-to-End ML Pipeline", "Create a complete ML pipeline with data ingestion, training, and deployment.", 200),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc3": [
        ("User Research Report", "Conduct 5 user interviews and synthesize findings into an actionable research report.", 100),
        ("Wireframe & Prototype", "Create low-fidelity wireframes and a clickable Figma prototype for a mobile app.", 150),
        ("Design System Creation", "Build a comprehensive design system with tokens, components, and documentation.", 150),
        ("Usability Testing", "Run usability tests with 5 participants and present findings with recommendations.", 100),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc4": [
        ("EC2 Web Server Setup", "Launch and configure an EC2 instance with a web server, security groups, and SSL.", 100),
        ("S3 Static Website Hosting", "Host a static website on S3 with CloudFront CDN and custom domain.", 100),
        ("Serverless Lambda Functions", "Build serverless APIs using AWS Lambda, API Gateway, and DynamoDB.", 150),
        ("CI/CD with CodePipeline", "Set up automated deployment pipeline for a sample application.", 150),
        ("Infrastructure as Code", "Define AWS infrastructure using Terraform or CloudFormation templates.", 150),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc5": [
        ("Todo App with React Native", "Build a cross-platform todo app with local storage and push notifications.", 100),
        ("Navigation & Routing", "Implement complex navigation with tabs, stacks, and drawers using React Navigation.", 100),
        ("API Integration", "Connect your app to a REST API with authentication and data fetching.", 150),
        ("Published App Store Build", "Prepare and submit your app to Expo or App Store / Play Store.", 150),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc6": [
        ("Dockerize an Application", "Containerize a Node.js app with multi-stage Dockerfile and docker-compose.", 100),
        ("Kubernetes Deployment", "Deploy an application to a local K8s cluster with services and ingress.", 150),
        ("GitHub Actions Workflow", "Create CI/CD workflows for testing, building, and deploying on push.", 100),
        ("Monitoring with Prometheus", "Set up application monitoring and alerting with Prometheus and Grafana.", 150),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc7": [
        ("Network Scanning Lab", "Perform network reconnaissance and vulnerability scanning on a test network.", 100),
        ("Penetration Test Report", "Conduct a web app penetration test and document findings with CVSS scores.", 150),
        ("Security Policy Document", "Draft an organizational security policy covering access control and incident response.", 100),
        ("CTF Challenge Writeup", "Complete 3 CTF challenges and document your methodology and solutions.", 150),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc8": [
        ("ERC-20 Token Contract", "Write, test, and deploy an ERC-20 token on a testnet using Hardhat.", 150),
        ("NFT Minting dApp", "Build a frontend for minting NFTs with MetaMask integration and IPFS storage.", 200),
        ("DeFi Yield Farming Simulator", "Create a simple DeFi protocol simulation with staking and rewards.", 200),
        ("Smart Contract Security Audit", "Audit a provided smart contract and report vulnerabilities.", 150),
    ],
    "cccccccc-cccc-cccc-cccc-ccccccccccc9": [
        ("Product Requirements Document", "Write a comprehensive PRD for a new feature with user stories and acceptance criteria.", 100),
        ("Agile Sprint Simulation", "Run a 2-week sprint simulation with planning, daily standups, and retrospective.", 100),
        ("Metrics Dashboard Design", "Define key metrics for a product and design a dashboard mockup.", 100),
        ("Stakeholder Presentation", "Prepare and deliver a product strategy presentation to simulated stakeholders.", 100),
    ],
    "cccccccc-cccc-cccc-cccc-cccccccccc10": [
        ("Async Programming Challenge", "Solve concurrency problems using asyncio, threading, and multiprocessing.", 100),
        ("Custom Decorators & Metaclasses", "Build advanced Python utilities using decorators and metaclasses.", 100),
        ("Performance Optimization", "Profile and optimize a slow Python application for 10x speedup.", 150),
        ("Python Package Publication", "Build and publish a reusable Python package to PyPI with proper tooling.", 100),
    ],
}

TASKS_DATA = [
    ("Review assignment submissions", "Go through all pending submissions and provide initial feedback.", "pending", "high"),
    ("Prepare lecture slides for Week 5", "Update slides with new examples and interactive exercises.", "completed", "medium"),
    ("1-on-1 with struggling students", "Schedule and conduct mentoring sessions with students below 50% progress.", "in_progress", "urgent"),
    ("Update course materials", "Refresh outdated content and add new resources to the learning platform.", "pending", "medium"),
    ("Grade mid-term projects", "Evaluate and score all mid-term submissions with detailed rubrics.", "completed", "high"),
    ("Record supplementary video", "Create a short tutorial video explaining a difficult concept.", "pending", "low"),
    ("Post-weekly announcement", "Write and publish the weekly course update and next steps.", "completed", "low"),
    ("Review peer feedback", "Go through peer-review assignments and moderate discussions.", "in_progress", "medium"),
    ("Set up office hours", "Configure calendar and meeting links for upcoming office hours.", "completed", "low"),
    ("Create quiz questions", "Draft 20 multiple-choice and coding quiz questions for next week.", "pending", "medium"),
    ("Analyze course analytics", "Review completion rates, engagement metrics, and student feedback.", "completed", "high"),
    ("Mentor onboarding session", "Welcome and brief new mentor joining the platform.", "pending", "low"),
]

MEETING_TITLES = [
    "Weekly Check-in", "Code Review Session", "Career Coaching", "Project Planning",
    "Debugging Help", "Mock Interview", "Portfolio Review", "Sprint Retrospective",
    "Thesis Discussion", "Industry Insights Chat", "Technical Deep Dive", "Resume Workshop",
]

MESSAGE_TEMPLATES = [
    "Hi! I had a question about the assignment due next week.",
    "Thanks for the feedback on my project! I'll make those changes.",
    "Can we reschedule our meeting to Thursday?",
    "I just submitted my assignment. Could you take a look when you have time?",
    "The lecture on async programming was really helpful, thanks!",
    "I'm struggling with the Docker setup. Could you point me to some resources?",
    "Great session today! I learned a lot about best practices.",
    "Quick question: should we use TypeScript for the final project?",
    "I've updated my portfolio based on your suggestions.",
    "Can you recommend any additional reading on neural networks?",
    "The CI/CD pipeline is failing and I'm not sure why. Here's the error log...",
    "Thank you for the extension on the assignment. I really appreciate it!",
    "I found a bug in the course material for Week 3. The code snippet has a typo.",
    "Would you be open to writing me a recommendation letter?",
    "I completed the extra credit challenge. It was tough but rewarding!",
]

NOTIFICATION_TEMPLATES = [
    ("Assignment Due Soon", "Your assignment '{}' is due in 48 hours. Don't forget to submit!", "assignment"),
    ("New Meeting Scheduled", "You have a new meeting: '{}' on {}. Add it to your calendar!", "meeting"),
    ("Feedback Received", "New feedback is available for your '{}' assignment.", "feedback"),
    ("Course Announcement", "New announcement from your mentor in '{}'. Check it out!", "info"),
    ("Progress Milestone", "Congratulations! You've reached {}% progress in '{}'. Keep it up!", "system"),
    ("Meeting Starting Soon", "Your meeting '{}' starts in 15 minutes. Join here: {}", "meeting"),
    ("Assignment Graded", "Your submission for '{}' has been graded. View your score!", "feedback"),
    ("Welcome to the Course", "Welcome to '{}'! Get started with the first module.", "info"),
    ("Weekly Reminder", "Weekly reminder: complete your pending tasks for '{}'.", "reminder"),
    ("New Course Available", "A new course '{}' is now open for enrollment!", "system"),
]

FEEDBACK_COMMENTS = [
    "Absolutely fantastic course! The projects were challenging but incredibly rewarding. Dr. Watson is an amazing instructor.",
    "Great content and structure. I wish there were more advanced topics in the later weeks, but overall excellent.",
    "The hands-on labs made all the difference. I went from zero to deploying real apps in just a few months.",
    "Well organized curriculum with clear learning objectives. The mentor support was top-notch.",
    "Best investment I've made in my career. The portfolio project helped me land my first developer job!",
    "Some modules felt rushed, but the community and mentor feedback more than made up for it.",
    "The real-world projects are what set this apart from other courses. Highly recommended!",
    "Incredible depth of content. I appreciated the focus on best practices and clean code.",
    "The pacing was perfect for working professionals. I could learn at my own speed while still being challenged.",
    "Outstanding course! The mix of theory and practice is exactly what I needed to level up my skills.",
    "Good introduction to the field. Would love a follow-up advanced course on the same topics.",
    "The mentor was incredibly responsive and provided detailed, actionable feedback on every assignment.",
    "I loved the peer review system. Getting feedback from classmates added so much value.",
    "The course materials are comprehensive and well-maintained. Everything worked without issues.",
    "Challenging but fair. The support from the teaching assistants was exceptional.",
]

PASSWORD_HASH = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

def generate_users_sql():
    lines = ["-- Admins"]
    values = []
    for uid, name, email in ADMINS:
        avatar = f"https://i.pravatar.cc/150?u={name.split()[0].lower()}"
        values.append(f"('{uid}', '{name}', '{email}', '{PASSWORD_HASH}', 'admin', '{avatar}', true, '2023-08-15T09:00:00Z')")
    lines.append("INSERT INTO users (id, name, email, password_hash, role, avatar_url, email_verified, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    
    lines.append("\n-- Mentors")
    values = []
    base_date = datetime(2023, 9, 1, 8, 0, 0)
    for i, (uid, name, email) in enumerate(MENTORS):
        avatar = f"https://i.pravatar.cc/150?u={name.split()[-1].lower()}"
        date = (base_date + timedelta(days=i)).isoformat() + "Z"
        values.append(f"('{uid}', '{name}', '{email}', '{PASSWORD_HASH}', 'mentor', '{avatar}', true, '{date}')")
    lines.append("INSERT INTO users (id, name, email, password_hash, role, avatar_url, email_verified, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    
    lines.append("\n-- Students")
    values = []
    base_date = datetime(2023, 10, 1, 8, 0, 0)
    for i, (uid, name, email) in enumerate(STUDENTS):
        avatar = f"https://i.pravatar.cc/150?u={email.split('@')[0].replace('.', '')}"
        date = (base_date + timedelta(days=i//2, hours=i%2)).isoformat() + "Z"
        values.append(f"('{uid}', '{name}', '{email}', '{PASSWORD_HASH}', 'student', '{avatar}', true, '{date}')")
    lines.append("INSERT INTO users (id, name, email, password_hash, role, avatar_url, email_verified, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    
    return "\n".join(lines)

def generate_courses_sql():
    lines = []
    values = []
    base_date = datetime(2023, 9, 10, 10, 0, 0)
    for i, (cid, title, desc, mid, weeks, price, rating, status) in enumerate(COURSES):
        date = (base_date + timedelta(days=i*2)).isoformat() + "Z"
        values.append(f"('{cid}', '{title}', '{desc}', '{mid}', {weeks}, {price}, {rating}, '{status}', '{date}')")
    lines.append("INSERT INTO courses (id, title, description, mentor_id, duration_weeks, price, rating, status, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    return "\n".join(lines)

def generate_enrollments_sql():
    lines = []
    values = []
    # Pre-defined enrollment data for realistic distribution
    enrollments = [
        # (student_idx, course_idx, progress, status, enrolled_offset_days, completed_offset_days)
        (0, 0, 85, "active", 15, None), (0, 3, 42, "active", 32, None), (0, 5, 10, "active", 102, None),
        (1, 0, 100, "completed", 15, 117), (1, 1, 67, "active", 41, None), (1, 4, 25, "active", 97, None),
        (2, 1, 92, "active", 20, None), (2, 2, 55, "active", 45, None), (2, 8, 30, "active", 107, None),
        (3, 0, 78, "active", 18, None), (3, 6, 45, "active", 62, None),
        (4, 2, 100, "completed", 22, 132), (4, 3, 38, "active", 42, None), (4, 7, 100, "completed", 46, 77),
        (5, 1, 72, "active", 25, None), (5, 4, 15, "active", 112, None), (5, 9, 5, "active", 124, None),
        (6, 0, 60, "active", 30, None), (6, 5, 88, "active", 56, None),
        (7, 2, 95, "active", 32, None), (7, 6, 50, "active", 71, None), (7, 8, 20, "active", 117, None),
        (8, 1, 100, "completed", 10, 102), (8, 3, 33, "active", 76, None),
        (9, 0, 48, "active", 36, None), (9, 4, 70, "active", 61, None),
        (10, 2, 100, "completed", 12, 104), (10, 5, 22, "active", 103, None), (10, 9, 12, "active", 128, None),
        (11, 1, 58, "active", 41, None), (11, 6, 80, "active", 81, None),
        (12, 0, 90, "active", 20, None), (12, 3, 15, "active", 106, None), (12, 7, 100, "completed", 6, 62),
        (13, 2, 65, "active", 51, None), (13, 4, 40, "active", 100, None),
        (14, 1, 100, "completed", 5, 93), (14, 5, 55, "active", 66, None), (14, 8, 75, "active", 108, None),
        (15, 0, 30, "active", 107, None), (15, 3, 62, "active", 57, None),
        (16, 2, 85, "active", 28, None), (16, 6, 18, "active", 120, None),
        (17, 1, 45, "active", 62, None), (17, 4, 95, "active", 15, None), (17, 9, 8, "active", 133, None),
        (18, 0, 70, "active", 46, None), (18, 5, 100, "completed", 1, 93),
        (19, 1, 25, "active", 117, None), (19, 3, 78, "active", 30, None), (19, 7, 100, "completed", 21, 71),
        (20, 2, 52, "active", 66, None), (20, 4, 35, "active", 122, None), (20, 9, 15, "active", 138, None),
        (21, 0, 68, "active", 56, None), (21, 6, 40, "active", 98, None),
        (22, 1, 82, "active", 36, None), (22, 5, 20, "active", 110, None), (22, 8, 45, "active", 82, None),
        (23, 2, 38, "active", 72, None), (23, 4, 60, "active", 46, None),
        (24, 0, 55, "active", 82, None), (24, 3, 28, "active", 95, None), (24, 7, 75, "active", 52, None),
    ]
    
    base_date = datetime(2023, 10, 1, 8, 0, 0)
    for s_idx, c_idx, progress, status, enrolled_days, completed_days in enrollments:
        sid = STUDENTS[s_idx][0]
        cid = COURSES[c_idx][0]
        enrolled_at = (base_date + timedelta(days=enrolled_days)).isoformat() + "Z"
        completed_at = (base_date + timedelta(days=completed_days)).isoformat() + "Z" if completed_days else "NULL"
        if completed_at == "NULL":
            values.append(f"('{sid}', '{cid}', {progress}, '{status}', '{enrolled_at}', NULL)")
        else:
            values.append(f"('{sid}', '{cid}', {progress}, '{status}', '{enrolled_at}', '{completed_at}')")
    
    lines.append("INSERT INTO enrollments (student_id, course_id, progress, status, enrolled_at, completed_at) VALUES")
    lines.append(",\n".join(values) + ";")
    return "\n".join(lines)

def generate_assignments_sql():
    lines = []
    values = []
    base_date = datetime(2023, 10, 15, 23, 59, 0)
    
    assign_id = 1
    for cid, items in ASSIGNMENT_TEMPLATES.items():
        for title, desc, max_score in items:
            due_offset = assign_id * 7
            due_date = (base_date + timedelta(days=due_offset)).isoformat() + "Z"
            status = "active" if due_offset > 200 else "completed"
            aid = f"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaa{assign_id:03d}"
            values.append(f"('{aid}', '{cid}', '{title}', '{desc}', '{due_date}', {max_score}, '{status}', '2023-10-01T10:00:00Z')")
            assign_id += 1
    
    lines.append("INSERT INTO assignments (id, course_id, title, description, due_date, max_score, status, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    return "\n".join(lines)

def generate_tasks_sql():
    lines = []
    values = []
    base_date = datetime(2024, 1, 15, 9, 0, 0)
    
    task_id = 1
    for mid, _name, _email in MENTORS:
        # Each mentor gets 4 tasks
        for i in range(4):
            tdata = TASKS_DATA[(task_id - 1) % len(TASKS_DATA)]
            title, desc, status, priority = tdata
            due_offset = task_id * 3
            due_date = (base_date + timedelta(days=due_offset)).isoformat() + "Z"
            completed_at = (base_date + timedelta(days=due_offset - 1)).isoformat() + "Z" if status == "completed" else "NULL"
            tid = f"tttttttt-tttt-tttt-tttt-ttttttttt{task_id:03d}"
            if completed_at == "NULL":
                values.append(f"('{tid}', '{mid}', '{title}', '{desc}', '{status}', '{priority}', '{due_date}', NULL, '2024-01-10T10:00:00Z')")
            else:
                values.append(f"('{tid}', '{mid}', '{title}', '{desc}', '{status}', '{priority}', '{due_date}', '{completed_at}', '2024-01-10T10:00:00Z')")
            task_id += 1
    
    lines.append("INSERT INTO tasks (id, mentor_id, title, description, status, priority, due_date, completed_at, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    return "\n".join(lines)

def generate_meetings_sql():
    lines = []
    values = []
    base_date = datetime(2024, 2, 1, 10, 0, 0)
    
    meeting_id = 1
    for i in range(30):
        mid = MENTORS[i % len(MENTORS)][0]
        sid = STUDENTS[i % len(STUDENTS)][0]
        title = MEETING_TITLES[i % len(MEETING_TITLES)]
        desc = f"1-on-1 mentoring session: {title.lower()}"
        mdate = (base_date + timedelta(days=i*2, hours=i%3)).isoformat() + "Z"
        duration = [30, 45, 60][i % 3]
        link = f"https://meet.jit.si/afg-session-{meeting_id:03d}"
        status = "scheduled" if i > 10 else ("completed" if i < 5 else "cancelled")
        m_uuid = f"mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmm{meeting_id:04d}"
        values.append(f"('{m_uuid}', '{mid}', '{sid}', '{title}', '{desc}', '{mdate}', {duration}, '{link}', '{status}', '2024-01-20T10:00:00Z')")
        meeting_id += 1
    
    lines.append("INSERT INTO meetings (id, mentor_id, student_id, title, description, meeting_datetime, duration_minutes, meeting_link, status, created_at) VALUES")
    lines.append(",\n".join(values) + ";")
    return "\n".join(lines)

def generate_messages_sql():
    lines = []
    values = []
    base_date = datetime(2024, 1, 15, 9, 0, 0)
    
    msg_id = 1
    # Create conversation threads between students and mentors
    for conv in range(20):
        student = STUDENTS[conv % len(STUDENTS)][0]
        mentor = MENTORS[conv % len(MENTORS)][0]
        num_messages = random.choice([3, 4, 5])
        for msg_in_conv in range(num_messages):
            # Alternate sender/receiver
            if msg_in_conv % 2 == 0:
                sender, receiver = student, mentor
            else:
                sender, receiver = mentor, student
            content = MESSAGE_TEMPLATES[(msg_id - 1) % len(MESSAGE_TEMPLATES)]
            sent_at = (base_date + timedelta(days=conv*2, hours=msg_in_conv)).isoformat() + "Z"
            read_at = (base_date + timedelta(days=conv*2, hours=msg_in_conv+1)).isoformat() + "Z" if msg_in_conv < num_messages - 1 else "NULL"
            m_uuid = f"mmmmmmmm-mmmm-mmmm-mmmm-mmmmmmmm{msg_id:04d}"
            if read_at == "NULL":
                values.append(f"('{m_uuid}', '{sender}', '{receiver}', '{content}', '{sent_at}', NULL)")
            else:
                values.append(f"('{m_uuid}', '{sender}', '{receiver}', '{content}', '{sent_at}', '{read_at}')")
            msg_id += 1
    
    # Admin-mentor conversations
    for conv in range(5
