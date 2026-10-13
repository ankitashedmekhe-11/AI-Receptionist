I need you to act as a SENIOR SOFTWARE ARCHITECT, TECHNICAL DOCUMENTATION ANALYST, and PROJECT RESEARCH ANALYST.

I am going to use the information you provide to create a formal academic/project report for my software/research project.

IMPORTANT:
DO NOT write the final project documentation yet.

Your first task is to deeply inspect my ENTIRE project and give me a complete, accurate, structured PROJECT CONTEXT PACKAGE that another AI can use to write the final documentation.

I want the context to be based on the ACTUAL implementation in my project files, code, configuration, database, diagrams, assets, and documentation — NOT assumptions.

==================================================
1. FIRST: UNDERSTAND THE ENTIRE PROJECT
==================================================

Inspect the complete project repository/workspace.

Go through:

- Source code
- Backend
- Frontend
- APIs
- Database
- Configuration files
- Environment/configuration structure
- Models
- Controllers
- Services
- Utilities
- AI/ML/CV modules
- Algorithms
- Business logic
- Authentication
- Validation
- Error handling
- Logging
- Storage
- File handling
- External integrations
- Dependencies
- UI components
- Pages/screens
- Workflows
- Any diagrams
- Any existing documentation
- README files
- Test files
- Sample data
- Configuration files
- Deployment files
- Docker files if present
- Scripts
- Generated outputs
- Important assets

Do NOT only inspect the README.

Trace the actual execution flow of the application wherever possible.

For example:

USER INPUT
→ FRONTEND
→ API REQUEST
→ BACKEND
→ PROCESSING/AI/ML
→ DATABASE/STORAGE
→ DECISION/RESULT
→ FRONTEND RESPONSE

Explain what actually happens at every important stage.

==================================================
2. DO NOT INVENT ANYTHING
==================================================

This is extremely important.

Only describe something as implemented if you can verify it from the project.

If something is:

- planned but not implemented
- partially implemented
- experimental
- commented out
- broken
- deprecated
- unused
- present in documentation but not actually implemented

clearly mark it.

Use labels such as:

[IMPLEMENTED]
[PARTIALLY IMPLEMENTED]
[EXPERIMENTAL]
[PLANNED]
[NOT VERIFIED]
[DEPRECATED]
[BROKEN/ISSUE]

Do not silently convert planned features into implemented features.

Do not claim an AI model, database, API, algorithm, security mechanism, or feature exists unless you find evidence in the project.

If something is unclear, explicitly say:

"Not verified from the available project files."

==================================================
3. IDENTIFY THE PROJECT PROPERLY
==================================================

Give me:

- Exact project name
- Project type
- Domain
- Problem being solved
- Target users
- Main purpose
- Core idea
- Main innovation/contribution
- Main modules
- Major workflows
- Technologies used
- Programming languages
- Frameworks
- Libraries
- Databases
- AI/ML/CV technologies
- APIs
- Infrastructure
- Deployment approach
- Development environment

Also explain the project in:

A. One sentence
B. 3–5 sentences
C. Simple explanation for a non-technical person
D. Technical explanation for a software engineer
E. Academic/research explanation

==================================================
4. EXTRACT THE ACTUAL ARCHITECTURE
==================================================

Create a detailed architecture description based on the actual implementation.

Identify:

- Frontend layer
- Backend layer
- API layer
- Processing layer
- AI/ML/CV layer
- Database layer
- Storage layer
- External services
- Authentication layer
- Logging/audit layer
- Any orchestration layer

Explain how each component communicates with the others.

Provide the architecture as:

User
↓
Frontend
↓
API
↓
Backend
↓
Processing / AI / Business Logic
↓
Database / Storage
↓
Result

But MODIFY this flow according to the actual project.

Also identify:

- Synchronous flows
- Asynchronous flows
- WebSocket flows
- WebRTC flows
- Background processing
- Streaming
- Queues
- Event-driven components

if they exist.

==================================================
5. COMPLETE MODULE BREAKDOWN
==================================================

Create a detailed module inventory.

For every module provide:

Module Name
Purpose
Input
Processing
Output
Dependencies
Important files
Important classes/functions
Current implementation status

Example:

MODULE:
Authentication

PURPOSE:
...

FILES:
...

INPUT:
...

PROCESSING:
...

OUTPUT:
...

STATUS:
[IMPLEMENTED]

Do this for EVERY major module.

==================================================
6. ACTUAL END-TO-END WORKFLOW
==================================================

Explain the complete user journey.

For example:

1. User opens application
2. User starts session
3. Frontend initializes camera
4. Backend creates session
5. Frames/data are transmitted
6. Processing begins
7. Quality checks occur
8. AI/CV processing occurs
9. Evidence is generated
10. Rules evaluate evidence
11. Result is produced
12. Frontend displays result
13. Audit/evidence information is stored

BUT DO NOT COPY THIS EXAMPLE.

Create the actual workflow from the code.

Include:

- Happy path
- Validation failures
- Error paths
- Retry behaviour
- Timeout behaviour
- Session termination
- Failure conditions
- Edge cases

==================================================
7. AI / ML / COMPUTER VISION ANALYSIS
==================================================

If the project contains AI, ML, Computer Vision, OCR, LLMs, agents, embeddings, RAG, GNNs, or other intelligent components, analyze them deeply.

For every AI/ML component identify:

- Model/algorithm name
- Framework/library
- Input
- Output
- Purpose
- Where it is called
- How it is configured
- Whether it is pretrained or trained
- Whether custom training exists
- Whether inference is local or remote
- Thresholds
- Confidence values
- Preprocessing
- Postprocessing
- Failure conditions
- Whether the output directly affects a final decision

VERY IMPORTANT:

Distinguish between:

1. AI/ML used to generate signals
2. AI/ML used for classification
3. Rule-based decision logic
4. Human decision
5. LLM-generated information
6. Deterministic validation

Do not mix these together.

If the project intentionally avoids AI-based final decision-making, explicitly document that architecture.

==================================================
8. ALGORITHMS AND LOGIC
==================================================

Identify every important algorithm or decision process.

For each one explain:

- Name
- Purpose
- Input
- Steps
- Formula if applicable
- Thresholds
- Output
- Failure conditions
- Where implemented in code

Convert important logic into clean academic pseudocode.

Do NOT invent mathematical formulas.

If an algorithm is implemented through multiple files/functions, trace the entire chain.

==================================================
9. DATABASE / DATA MODEL
==================================================

Analyze the actual database.

Identify:

- Database technology
- Database name if available
- Collections/tables
- Fields
- Data types
- Primary keys
- Foreign keys
- Relationships
- Indexes
- Constraints
- Validation
- Important queries
- Read/write operations

Create a database schema table:

Table/Collection
Field
Type
Purpose
Required?
Relationship

Also explain the database relationships.

If MongoDB is used, explain collections and document structure instead of forcing relational terminology.

==================================================
10. API DOCUMENTATION
==================================================

Extract all important API endpoints.

For each endpoint provide:

Method
Endpoint
Purpose
Authentication
Request parameters/body
Response
Success response
Error response
Files/functions involved

Also identify:

- WebSocket endpoints
- WebRTC endpoints
- Streaming endpoints
- Internal APIs

if present.

==================================================
11. REQUIREMENTS
==================================================

Based ONLY on the actual system, create:

Functional Requirements

FR-01
FR-02
FR-03
...

For each:

ID
Requirement
Description
Actual implementation evidence

Also create:

Non-Functional Requirements

NFR-01
NFR-02
...

Cover:

- Performance
- Security
- Reliability
- Usability
- Maintainability
- Scalability
- Availability
- Privacy
- Data integrity
- Compatibility

Only include requirements that are actually applicable.

==================================================
12. HARDWARE AND SOFTWARE REQUIREMENTS
==================================================

Identify the realistic requirements for running/developing the actual project.

Include:

Hardware:
- CPU
- RAM
- GPU if required
- Camera
- Storage
- Network

Software:
- OS
- Programming languages
- Runtime versions
- Frameworks
- Libraries
- Databases
- Development tools
- Browser
- External dependencies

Separate:

Development requirements
Runtime requirements
Optional requirements

==================================================
13. FEASIBILITY
==================================================

Analyze:

Technical Feasibility
Operational Feasibility
Economic Feasibility

Base this on the actual technology stack.

Do not exaggerate.

If the system requires paid services, mention them.

If it uses free/open-source components, identify them.

==================================================
14. SECURITY AND PRIVACY
==================================================

Analyze actual implementation.

Identify:

- Authentication
- Authorization
- Session management
- Password handling
- Encryption
- Data masking
- Secrets management
- Input validation
- API security
- CORS
- Rate limiting
- Logging
- Audit trails
- Data retention
- Sensitive data handling
- Privacy protections

IMPORTANT:

Do not claim something is secure simply because the project intends it to be secure.

Separate:

IMPLEMENTED SECURITY
from
RECOMMENDED SECURITY
from
MISSING SECURITY

==================================================
15. TESTING
==================================================

Inspect actual tests and testing-related files.

Identify:

- Unit tests
- Integration tests
- API tests
- UI tests
- Manual testing
- Performance testing
- Edge-case testing
- Error testing

Create a test case structure:

Test Case ID
Module
Test Scenario
Input
Expected Result
Actual Result
Status

Only report actual results if they are available.

Do not fabricate successful test results.

==================================================
16. CURRENT ISSUES / LIMITATIONS
==================================================

This section is extremely important.

Find:

- Bugs
- Broken modules
- Incomplete features
- TODOs
- Hardcoded values
- Temporary implementations
- Performance bottlenecks
- Security gaps
- Dependency problems
- Error handling gaps
- Scalability limitations
- Accuracy limitations
- Data limitations

Explain the impact of each issue.

==================================================
17. FUTURE SCOPE
==================================================

Based on the actual architecture, identify realistic future improvements.

Separate:

- Immediate improvements
- Medium-term improvements
- Research-level improvements
- Production-level improvements

Do not list random generic AI features.

Future scope must logically follow from the existing project.

==================================================
18. RESEARCH / ACADEMIC CONTRIBUTION
==================================================

If this project is a research-oriented project, identify:

- Research problem
- Research objectives
- Existing problem/gap
- Proposed approach
- Novel components
- Technical contribution
- Evaluation approach
- Expected/observed contribution
- Limitations

Clearly distinguish:

WHAT THE PROJECT ACTUALLY IMPLEMENTS

from

WHAT COULD BE CLAIMED AS FUTURE WORK.

==================================================
19. DIAGRAMS REQUIRED FOR FINAL DOCUMENTATION
==================================================

Based on the actual architecture, tell me which diagrams should be included.

Consider:

1. System Architecture Diagram
2. Use Case Diagram
3. Class Diagram
4. Object Diagram
5. Sequence Diagram
6. Activity Diagram
7. Component Diagram
8. Deployment Diagram
9. ER Diagram / Database Diagram
10. Data Flow Diagram
11. Workflow Diagram
12. AI/ML Pipeline Diagram

For each diagram explain:

- Whether it is applicable
- What entities/components should appear
- What relationships should be shown
- What the diagram should communicate

Do NOT invent entities that don't exist.

==================================================
20. SCREENSHOTS / UI DOCUMENTATION
==================================================

Inspect the actual frontend and identify important screens/pages.

For every screen provide:

Figure Number suggestion
Screen/Page Name
Purpose
Main UI elements
User action
System response

Create a logical screenshot sequence for the final report.

==================================================
21. REFERENCES / SOURCES
==================================================

Identify existing:

- Research papers
- Documentation
- Framework references
- Libraries
- APIs
- Standards
- Technical references

already present in the project.

Do not invent citations.

If a reference exists only as a URL, record it.

==================================================
22. FINAL MASTER PROJECT CONTEXT
==================================================

At the end, produce ONE consolidated section called:

"MASTER PROJECT CONTEXT FOR DOCUMENTATION"

This should contain everything another AI needs to write the final report.

Structure it as:

1. Project Identity
2. Project Summary
3. Problem Statement
4. Objectives
5. Scope
6. Target Users
7. Key Features
8. Technology Stack
9. Architecture
10. Modules
11. End-to-End Workflow
12. AI/ML Components
13. Algorithms
14. Database
15. APIs
16. Security
17. Requirements
18. Testing
19. Results/Current State
20. Limitations
21. Future Scope
22. Diagrams Required
23. Screenshots Required
24. References
25. Implementation Status
26. Known Issues
27. Important Technical Details
28. Anything Else Needed for Formal Documentation

==================================================
23. IMPORTANT: PREPARE IT FOR THIS REPORT FORMAT
==================================================

The final documentation will follow a formal academic project-report structure similar to this:

PROJECT REPORT

TITLE PAGE

ABSTRACT

LIST OF FIGURES

LIST OF TABLES

LIST OF ABBREVIATIONS

CHAPTER 1 — INTRODUCTION
1.1 Background and Motivation
1.2 Problem Statement
1.3 Objectives and Scope
1.3.1 Objectives
1.3.2 Scope
1.4 Organization of the Report

CHAPTER 2 — LITERATURE SURVEY / RELATED WORK
2.1 Review of Existing Systems and Techniques
2.2 Comparative Analysis
2.3 Research Gap and Proposed System

CHAPTER 3 — SOFTWARE REQUIREMENTS SPECIFICATION
3.1 Functional Requirements
3.2 Non-Functional Requirements
3.3 System Specifications
3.3.1 Hardware Specification
3.3.2 Software Specification
3.4 Feasibility Study
3.4.1 Technical Feasibility
3.4.2 Operational Feasibility
3.4.3 Economic Feasibility

CHAPTER 4 — SYSTEM DESIGN AND ARCHITECTURE
4.1 High-Level Architecture
4.2 System Modules
4.3 UML / System Diagrams
4.4 Database Design
4.5 Algorithmic and Functional Flow

CHAPTER 5 — IMPLEMENTATION AND METHODOLOGIES
5.1 Implementation Overview
5.2 Technologies and Development Environment
5.3 Module Implementation
5.4 Important Algorithms / Processing Logic
5.5 Integration

CHAPTER 6 — SOFTWARE TESTING AND QUALITY ASSURANCE
6.1 Testing Strategy
6.2 Test Cases
6.3 Functional Testing
6.4 Integration Testing
6.5 Performance / Accuracy Testing
6.6 Test Results

CHAPTER 7 — RESULTS, EVALUATION AND DISCUSSION
7.1 Implemented System
7.2 User Interface
7.3 Results
7.4 Evaluation
7.5 Discussion

CHAPTER 8 — CONCLUSION AND FUTURE SCOPE
8.1 Conclusion
8.2 Limitations
8.3 Future Scope

REFERENCES

APPENDICES

The FINAL DOCUMENTATION should retain this overall structure and academic style.

Your job right now is NOT to write this report.

Your job is to give me the COMPLETE VERIFIED CONTENT that can later be mapped into this structure.

==================================================
24. QUALITY RULES
==================================================

Follow these rules strictly:

1. Inspect the entire project before producing the final context.
2. Do not rely only on filenames.
3. Trace important code execution.
4. Do not invent implementation details.
5. Do not turn future plans into implemented features.
6. Clearly identify incomplete or broken components.
7. Preserve actual technical terminology used by the project.
8. Explain complicated technical concepts in both technical and simple language.
9. Use tables wherever structured information is easier to understand.
10. Include file paths for important implementation evidence.
11. Mention important class names, function names, APIs, models, schemas, and configuration values.
12. Identify dependencies between modules.
13. Identify contradictions between documentation and implementation.
14. Identify duplicate or obsolete implementations.
15. Identify hardcoded values and configurable values.
16. Do not hide limitations.
17. Do not fabricate metrics, accuracy, test results, performance numbers, citations, or research claims.
18. If a value cannot be verified, explicitly mark it as NOT VERIFIED.
19. Prefer actual implementation evidence over README descriptions.
20. Keep the output detailed enough that another AI can write a complete 70–100 page academic project report from it without needing to rediscover the project.

==================================================
25. FINAL OUTPUT FORMAT
==================================================

Give me the response in the following order:

A. PROJECT SNAPSHOT

B. ONE-PARAGRAPH PROJECT EXPLANATION

C. COMPLETE TECHNOLOGY STACK

D. PROJECT ARCHITECTURE

E. COMPLETE MODULE BREAKDOWN

F. END-TO-END WORKFLOW

G. AI/ML/CV/ALGORITHM ANALYSIS

H. DATABASE / DATA MODEL

I. API INVENTORY

J. FUNCTIONAL REQUIREMENTS

K. NON-FUNCTIONAL REQUIREMENTS

L. HARDWARE & SOFTWARE REQUIREMENTS

M. SECURITY & PRIVACY

N. TESTING

O. CURRENT IMPLEMENTATION STATUS

P. KNOWN ISSUES / LIMITATIONS

Q. FUTURE SCOPE

R. RESEARCH CONTRIBUTION

S. DIAGRAMS REQUIRED

T. SCREENSHOTS REQUIRED

U. REFERENCES / SOURCES

V. CONTRADICTIONS / UNCERTAINTIES

W. MASTER PROJECT CONTEXT FOR DOCUMENTATION

At the very end, add:

"DOCUMENTATION READINESS CHECK"

with:

- Information completely verified
- Information partially verified
- Information missing
- Information that requires user confirmation

Do NOT write the final academic report yet.

I want the output to be the most complete technical understanding of my project possible so that I can give your response to another AI and have it generate a polished academic project report without losing the actual technical details of the implementation.