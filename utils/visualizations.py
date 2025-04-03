import matplotlib.pyplot as plt
from database import db

def generate_productivity_chart(username: str, filename: str = "productivity.png"):
    """Generate visual report with theme support"""
    try:
        # Get user settings
        user_settings = db.get_user_settings(username)
        theme = user_settings.get("theme", "light")
        
        # Theme configuration
        colors = {
            "light": {
                "bg": "#FFFFFF", "text": "#000000",
                "colors": ["#4CAF50", "#FFC107", "#2196F3"]
            },
            "dark": {
                "bg": "#121212", "text": "#FFFFFF", 
                "colors": ["#2E7D32", "#FF8F00", "#1565C0"]
            }
        }.get(theme, "light")
        
        # Get stats
        from utils.stats import get_user_productivity
        stats = get_user_productivity(username)
        
        # Prepare data
        categories = ["Completed", "Pending", "Overdue"]
        values = [
            stats['completion_rate'] * stats['total_tasks'],
            (1 - stats['completion_rate']) * stats['total_tasks'],
            stats['overdue_tasks']
        ]
        
        # Create figure
        plt.style.use("dark_background" if theme == "dark" else "default")
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(colors["bg"])
        
        # Create chart
        bars = ax.bar(categories, values, color=colors["colors"])
        ax.set_title("Task Summary", color=colors["text"])
        ax.set_ylabel("Number of Tasks", color=colors["text"])
        ax.tick_params(axis='both', colors=colors["text"])
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', color=colors["text"])
        
        plt.tight_layout()
        plt.savefig(filename, facecolor=colors["bg"])
        plt.close()
        return True
    except Exception as e:
        print(f"❌ Visualization error: {str(e)}")
        return False