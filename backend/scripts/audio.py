import sys
from pathlib import Path

# Add parent directory to path so we can import planned
sys.path.insert(0, str(Path(__file__).parent.parent))

from planned.infrastructure.utils import youtube

if __name__ == "__main__":
    youtube.play_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
