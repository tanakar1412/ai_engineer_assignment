import json
import networkx as nx
from typing import List, Dict

class SkillsGraphEngine:
    def __init__(self, data_path: str):
        self.graph = nx.DiGraph()
        self.load_data(data_path)

    def load_data(self, data_path: str):
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Ingest Nodes [cite: 19, 20]
        for s in data.get('sectors', []): self.graph.add_node(s['id'], type='Sector', **s)
        for t in data.get('skill_tracks', []): self.graph.add_node(t['id'], type='Track', **t)
        for sk in data.get('skills', []): self.graph.add_node(sk['id'], type='Skill', **sk)
        for r in data.get('job_roles', []): self.graph.add_node(r['id'], type='Role', **r)
        for c in data.get('courses', []): self.graph.add_node(c['id'], type='Course', **c)

        # 2. Ingest Explicit Edges [cite: 26-30]
        edges = data.get('edges', {})
        for e in edges.get('sector_has_track', []):
            self.graph.add_edge(e['source'], e['target'], relation='HAS_SKILL_TRACK')
        for e in edges.get('skill_required_by_role', []):
            self.graph.add_edge(e['source'], e['target'], relation='REQUIRED_BY_ROLE')
        for e in edges.get('skill_prerequisite_of', []):
            self.graph.add_edge(e['source'], e['target'], relation='PREREQUISITE_OF')

        # 3. Ingest Implicit Edges [cite: 28, 31]
        for sk in data.get('skills', []):
            for t_id in sk.get('track_ids', []):
                self.graph.add_edge(t_id, sk['id'], relation='CONTAINS_SKILL')
        for c in data.get('courses', []):
            for s_id in c.get('skill_ids', []):
                self.graph.add_edge(c['id'], s_id, relation='TEACHES_SKILL')

    def get_learning_path(self, current_skills: List[str], target_role: str) -> List[str]:
        """Calculates path respecting prerequisites, ranked by SDFE priority."""
        if target_role not in self.graph:
            return []

        required_skills = [u for u, v, d in self.graph.in_edges(target_role, data=True) if d.get('relation') == 'REQUIRED_BY_ROLE']
        
        all_needed = set()
        for sk in required_skills:
            ancestors = {n for n in nx.ancestors(self.graph, sk) if self.graph.nodes[n].get('type') == 'Skill'}
            all_needed.update(ancestors)
            all_needed.add(sk)

        gaps = list(all_needed - set(current_skills))
        
        # Build prerequisite subgraph to ensure logical learning order
        subgraph = self.graph.subgraph(gaps)
        prereq_dag = nx.DiGraph([(u, v) for u, v, d in subgraph.edges(data=True) if d.get('relation') == 'PREREQUISITE_OF'])
        prereq_dag.add_nodes_from(gaps)

        # Tie-breaker: Prioritise SDFE priority == True, then lower difficulty
        def priority_sort(node):
            node_data = self.graph.nodes[node]
            priority = node_data.get('sdfe_priority', False)
            diff_map = {"Foundation": 1, "Intermediate": 2, "Advanced": 3}
            diff = diff_map.get(node_data.get('difficulty'), 4)
            return (not priority, diff)

        try:
            return list(nx.lexicographical_topological_sort(prereq_dag, key=priority_sort))
        except nx.NetworkXUnfeasible:
            return gaps # Fallback for cyclic data

    def get_gap_analysis(self, current_skills: List[str], target_role: str) -> List[Dict]:
        ordered_gaps = self.get_learning_path(current_skills, target_role)
        analysis = []
        for s_id in ordered_gaps:
            s_node = self.graph.nodes[s_id]
            course_ids = [u for u, v, d in self.graph.in_edges(s_id, data=True) if d.get('relation') == 'TEACHES_SKILL']
            courses = [{"id": c, "name": self.graph.nodes[c]['name']} for c in course_ids]
            
            analysis.append({
                "skill": s_node['name'],
                "priority": s_node.get('sdfe_priority', False),
                "courses": courses
            })
        return analysis

    def get_transferable_skills(self, source_economy: str, target_economy: str) -> List[Dict]:
        """Finds high-transferability skills originating in the source economy."""
        transferable = []
        for n, data in self.graph.nodes(data=True):
            if data.get('type') == 'Skill':
                # Look for skills in the SOURCE economy that are highly transferable
                if data.get('economy') == source_economy and data.get('transferability') == 'High':
                    transferable.append({"id": n, "name": data['name'], "economy": data['economy']})
        return transferable

    def export_visualisation(self, output_file="visualisation.html"):
        """Bonus Part D: Generates an interactive HTML network graph."""
        from pyvis.network import Network
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        
        color_map = {'Sector': '#e74c3c', 'Track': '#e67e22', 'Skill': '#3498db', 'Role': '#9b59b6', 'Course': '#2ecc71'}
        for node, data in self.graph.nodes(data=True):
            n_type = data.get('type', 'Unknown')
            net.add_node(node, label=data.get('name', node), title=f"Type: {n_type}", color=color_map.get(n_type, '#ffffff'))
            
        for u, v, d in self.graph.edges(data=True):
            net.add_edge(u, v, title=d.get('relation', ''))
            
        net.write_html(output_file)