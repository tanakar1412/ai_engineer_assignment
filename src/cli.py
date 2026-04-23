import argparse
import os
from src.graph_engine import SkillsGraphEngine
from src.llm_agent import LLMAgent

def main():
    parser = argparse.ArgumentParser(description="SkillsFuture Career Graph Interface")
    parser.add_argument("--data", default="data/skillsfuture_dataset.json", help="Path to JSON data")
    parser.add_argument("--visualise", action="store_true", help="Generate HTML graph visualization")
    parser.add_argument("--query", type=str, help="Natural language query")
    args = parser.parse_args()

    engine = SkillsGraphEngine(args.data)
    print(f"Graph loaded: {engine.graph.number_of_nodes()} nodes, {engine.graph.number_of_edges()} edges.")

    if args.visualise:
        engine.export_visualisation()
        print("Visualisation exported to visualisation.html")

    if args.query:
        agent = LLMAgent(api_key=os.getenv("OPENAI_API_KEY", ""), graph_engine=engine)
        response = agent.execute_query(args.query)
        print(f"\n[LLM Response]:\n{response}\n")
    else:
        # Default Demo (Gap Analysis)
        print("\n--- Running Demo Gap Analysis ---")
        gaps = engine.get_gap_analysis(["SKL-01", "SKL-03"], "ROL-02")
        for g in gaps:
            priority = "⭐ (SDFE Priority)" if g['priority'] else ""
            courses = ", ".join([c['name'] for c in g['courses']])
            print(f"- {g['skill']} {priority}\n  Recommended: {courses}\n")

if __name__ == "__main__":
    main()