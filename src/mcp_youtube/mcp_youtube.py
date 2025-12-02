import mcp.types as types
from mcp.server.fastmcp import FastMCP

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
from youtube_transcript_api._transcripts import Transcript
from urllib.parse import urlparse, parse_qs
import pydantic

# Create server instance
server = FastMCP("youtube-transcript")

class YoutubeTranscript(pydantic.BaseModel):
    video_url: str
    with_timestamps: bool = False
    language: str = "en"

def extract_video_id(url: str) -> str:
    """Extract video ID from various forms of YouTube URLs."""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path[1:]
    if parsed.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        elif parsed.path.startswith('/v/'):
            return parsed.path[3:]
        elif parsed.path.startswith('/shorts/'):
            return parsed.path[8:]
    raise ValueError("Could not extract video ID from URL")

@server.tool()
def get_transcript(video_id: str, with_timestamps: bool = False, language: str = "en") -> str:
    """Get transcript for a video ID and format it as readable text."""
    transcript: Transcript = None
    api = YouTubeTranscriptApi()
    available_transcripts = api.list(video_id)
    try:
        transcript = available_transcripts.find_transcript([language])
    except NoTranscriptFound:
        for t in available_transcripts:
            transcript = t
            break
        else:
            return f"No transcript found for video {video_id}"
    transcript = transcript.fetch()
    if with_timestamps:
        def format_timestamp(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            if hours > 0:
                return f"[{hours}:{minutes:02d}:{secs:02d}]"
            return f"[{minutes}:{secs:02d}]"
            
        return "\n".join(f"{format_timestamp(entry.start)} {entry.text}" for entry in transcript)
    else:
        return "\n".join(entry.text for entry in transcript)

def main():
    server.run()

if __name__ == "__main__":
    main()
