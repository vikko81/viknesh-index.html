import os
import shutil
import uuid
import logging
from typing import Dict, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import ffmpeg
from pydantic import BaseModel
import time

app = FastAPI(title="Vikas AI Video Processing Platform",
              description="Professional Video Editing API by Vikas")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    def __init__(self):
        self.UPLOAD_DIR = "uploads"
        self.OUTPUT_DIR = "outputs"
        self.TEMP_DIR = "temp"
        self.LOGS_DIR = "logs"
        self.ALLOWED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        self.MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
        
        # Create directories if they don't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.LOGS_DIR, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            filename=os.path.join(self.LOGS_DIR, 'vikas_ai.log'),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
config = Config()
logger = logging.getLogger("VikasAI")

class VideoProcessor:
    def __init__(self, input_path: str):
        self.input_path = input_path
        self.temp_files = []
        logger.info(f"Initialized VideoProcessor for {input_path}")

    def cleanup(self):
        """Remove all temporary files"""
        for file in self.temp_files:
            try:
                os.remove(file)
                logger.info(f"Removed temp file: {file}")
            except Exception as e:
                logger.warning(f"Failed to remove temp file {file}: {str(e)}")

    def enhance_video(self, output_path: str, options: Dict) -> str:
        """Apply video enhancements using FFmpeg"""
        try:
            logger.info(f"Enhancing video with options: {options}")
            
            # Basic enhancement filters
            filters = []
            if options.get('denoise'):
                filters.append('hqdn3d=1.5:1.5:6:6')
            if options.get('sharpen'):
                filters.append('unsharp=5:5:0.8:3:3:0.4')
            if options.get('color_correct'):
                filters.append('eq=contrast=1.05:brightness=0.02:saturation=1.05')
            
            # Build FFmpeg command
            input_stream = ffmpeg.input(self.input_path)
            video = input_stream.video
            
            if filters:
                video = video.filter(*filters)
            
            output = ffmpeg.output(
                video,
                input_stream.audio,
                output_path,
                vcodec='libx264',
                preset='fast',
                crf=23,
                acodec='aac',
                audio_bitrate='192k'
            )
            
            output.run(overwrite_output=True)
            logger.info(f"Enhanced video saved to {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise RuntimeError(f"Video enhancement failed: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Enhancement error: {str(e)}")
            raise

    def remove_watermark(self, output_path: str) -> str:
        """Placeholder for watermark removal (would use AI in production)"""
        try:
            logger.info("Running watermark removal (placeholder)")
            # In production, this would call an AI service
            shutil.copy2(self.input_path, output_path)
            return output_path
        except Exception as e:
            logger.error(f"Watermark removal error: {str(e)}")
            raise

    def extract_audio(self, output_path: str, format: str = 'mp3') -> str:
        """Extract audio from video"""
        try:
            logger.info(f"Extracting audio to {output_path}")
            
            input_stream = ffmpeg.input(self.input_path)
            audio = input_stream.audio
            
            output = ffmpeg.output(
                audio,
                output_path,
                acodec='libmp3lame' if format == 'mp3' else 'aac',
                audio_bitrate='192k'
            ).overwrite_output()
            
            output.run()
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Audio extraction failed: {e.stderr.decode()}")
            raise RuntimeError(f"Audio extraction failed: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Audio extraction error: {str(e)}")
            raise

    def create_short(self, output_path: str, duration: int = 30) -> str:
        """Create a short clip from the video"""
        try:
            logger.info(f"Creating {duration}s short clip")
            
            input_stream = ffmpeg.input(self.input_path)
            output = ffmpeg.output(
                input_stream.trim(start=0, duration=duration),
                output_path,
                vcodec='libx264',
                preset='fast',
                crf=23
            ).overwrite_output()
            
            output.run()
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Short creation failed: {e.stderr.decode()}")
            raise RuntimeError(f"Short creation failed: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Short creation error: {str(e)}")
            raise

    def replace_audio(self, audio_path: str, output_path: str) -> str:
        """Replace video audio track"""
        try:
            logger.info(f"Replacing audio with {audio_path}")
            
            video_input = ffmpeg.input(self.input_path)
            audio_input = ffmpeg.input(audio_path)
            
            output = ffmpeg.output(
                video_input.video,
                audio_input.audio,
                output_path,
                vcodec='copy',
                acodec='aac',
                shortest=None
            ).overwrite_output()
            
            output.run()
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"Audio replacement failed: {e.stderr.decode()}")
            raise RuntimeError(f"Audio replacement failed: {e.stderr.decode()}")
        except Exception as e:
            logger.error(f"Audio replacement error: {str(e)}")
            raise

# API Endpoints
@app.post("/upload")
async def upload_video(video: UploadFile = File(...), voice: Optional[UploadFile] = File(None)):
    """Handle video and optional voice sample upload"""
    try:
        # Validate video file
        file_ext = os.path.splitext(video.filename)[1].lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(400, "Invalid file type. Only video files are allowed.")
        
        # Save video file
        video_filename = f"video_{uuid.uuid4()}{file_ext}"
        video_path = os.path.join(config.UPLOAD_DIR, video_filename)
        
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
        
        # Save voice file if provided
        voice_filename = None
        if voice:
            voice_ext = os.path.splitext(voice.filename)[1].lower()
            if voice_ext not in ['.wav', '.mp3']:
                raise HTTPException(400, "Invalid voice file type. Only WAV/MP3 allowed.")
            
            voice_filename = f"voice_{uuid.uuid4()}{voice_ext}"
            voice_path = os.path.join(config.UPLOAD_DIR, voice_filename)
            
            with open(voice_path, "wb") as buffer:
                shutil.copyfileobj(voice.file, buffer)
        
        logger.info(f"Uploaded video: {video_filename}")
        if voice_filename:
            logger.info(f"Uploaded voice: {voice_filename}")
        
        return JSONResponse({
            "success": True,
            "video": video_filename,
            "voice": voice_filename
        })
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(500, f"Upload failed: {str(e)}")

class ProcessRequest(BaseModel):
    filename: str
    voice_file: Optional[str] = None
    enhance: bool = True
    remove_watermark: bool = False
    replace_voice: bool = False
    create_short: bool = True

@app.post("/process")
async def process_video(request: ProcessRequest):
    """Process video with given options"""
    job_id = str(uuid.uuid4())
    logger.info(f"Starting job {job_id} for {request.filename}")
    
    try:
        # Validate input file
        input_path = os.path.join(config.UPLOAD_DIR, request.filename)
        if not os.path.exists(input_path):
            raise HTTPException(404, "Video file not found")
        
        processor = VideoProcessor(input_path)
        base_name = os.path.splitext(request.filename)[0]
        timestamp = str(int(time.time()))
        
        # Prepare output paths
        outputs = {
            "enhanced": os.path.join(config.OUTPUT_DIR, f"{base_name}_enhanced_{timestamp}.mp4"),
            "no_watermark": os.path.join(config.OUTPUT_DIR, f"{base_name}_nowm_{timestamp}.mp4"),
            "audio": os.path.join(config.OUTPUT_DIR, f"{base_name}_audio_{timestamp}.mp3"),
            "short": os.path.join(config.OUTPUT_DIR, f"{base_name}_short_{timestamp}.mp4"),
            "final": os.path.join(config.OUTPUT_DIR, f"{base_name}_final_{timestamp}.mp4")
        }
        
        # Processing pipeline
        # 1. Enhance video
        processor.enhance_video(outputs["enhanced"], {
            "denoise": request.enhance,
            "sharpen": request.enhance,
            "color_correct": request.enhance
        })
        
        # 2. Remove watermark (placeholder)
        processor.remove_watermark(outputs["no_watermark"])
        
        # 3. Extract audio
        processor.extract_audio(outputs["audio"])
        
        # 4. Create short clip
        if request.create_short:
            processor.create_short(outputs["short"], 30)
        
        # 5. Voice replacement
        if request.replace_voice and request.voice_file:
            voice_path = os.path.join(config.UPLOAD_DIR, request.voice_file)
            if os.path.exists(voice_path):
                processor.replace_audio(voice_path, outputs["final"])
            else:
                logger.warning("Voice file not found, skipping replacement")
                shutil.copy2(outputs["no_watermark"], outputs["final"])
        else:
            shutil.copy2(outputs["no_watermark"], outputs["final"])
        
        # Cleanup
        processor.cleanup()
        
        # Prepare download URLs
        download_base = "/download/"
        response = {
            "success": True,
            "job_id": job_id,
            "downloads": {
                "enhanced": download_base + os.path.basename(outputs["enhanced"]),
                "no_watermark": download_base + os.path.basename(outputs["no_watermark"]),
                "audio": download_base + os.path.basename(outputs["audio"]),
                "short": download_base + os.path.basename(outputs["short"]),
                "final": download_base + os.path.basename(outputs["final"])
            }
        }
        
        logger.info(f"Job {job_id} completed successfully")
        return JSONResponse(response)
    
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Serve processed files for download"""
    try:
        file_path = os.path.join(config.OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(404, "File not found")
        
        return FileResponse(
            file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Download failed for {filename}: {str(e)}")
        raise HTTPException(500, f"Download failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Service health check"""
    return {"status": "healthy", "service": "Vikas AI Video Processor"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)