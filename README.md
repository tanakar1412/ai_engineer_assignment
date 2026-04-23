# AI Engineer Take-Home: Skills Graph System

## Setup Instructions
A reader can run this system in under 2 minutes.
1. `pip install -r requirements.txt`
2. Run default demo (Gap Analysis): `python -m src.cli`
3. Test Natural Language Query: `python -m src.cli --query "Which Digital skills are most transferable to Green?"`
4. Generate Visualisation (Bonus): `python -m src.cli --visualise`

## Design Document & Architecture

### A. Graph Schema Design Choices
The data was modeled as a **Directed Acyclic Graph (DAG)** using NetworkX. 
- **Explicit Edges:** `PREREQUISITE_OF` and `REQUIRED_BY_ROLE` are strictly directional to support pathfinding logic.
- **Embedded Lists to Edges:** Node arrays (e.g., `skill_ids` inside Courses) were converted during ingestion into explicit `TEACHES_SKILL` edges to allow native graph traversals rather than inefficient list lookups.

### B. Logic & Trade-offs
- **Pathfinding:** Rather than standard Shortest Path (which attempts to skip nodes to find the fastest physical route), I implemented **Lexicographical Topological Sorting**. This ensures the learner respects strict prerequisite chains (e.g., Python -> Machine Learning).
- **Tie-Breakers:** The sort function natively prioritizes skills where `sdfe_priority == True`, fulfilling the requirement to rank gaps by priority.
- **LLM Pipeline:** Implemented a Semantic Router pattern (Parse Intent -> Graph Native Query -> NL Formatter) to eliminate hallucination risks associated with Text-to-Cypher or raw graph prompting. 

### C. Scaling to Full SkillsFuture Framework
The full framework contains 38 sectors, 119+ job roles, and 80+ skills. 
- **Storage:** NetworkX is an in-memory tool. To scale, the schema translates directly to **Neo4j**, enabling ACID compliance and sub-millisecond Cypher traversals.
- **Search:** To handle thousands of real-world text variations (e.g., a user saying "I know how to code websites" instead of matching `SKL-17`), I would integrate an embedding database (like Qdrant or Neo4j Vector Index) for semantic node matching during the intent parsing phase.