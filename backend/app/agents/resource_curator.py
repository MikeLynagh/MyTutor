class ResourceCuratorAgent: 
    def curate(self, goal: str, source_mode: str, user_material: str | None = None):
        return {
            "sources": [
                {
                    "title": "Beginner Rubix cube guide", 
                    "url": "https://solvethecube.com/", 
                    "reason": "Clear beginner-friendly steps"
                }, 
                {
                    "title": "Cube notation basics",  
                    "url": "https://ruwix.com/the-rubiks-cube/how-to-solve-the-rubiks-cube-beginners-method/",
                    "reason": "high rank on Google"
                }
            ], 
            "summary": "Typical beginner summary methods solve the cube in steps "
        }