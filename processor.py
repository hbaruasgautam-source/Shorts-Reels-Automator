import os
# Added CompositeVideoClip to imports
from moviepy.editor import VideoFileClip, clips_array, CompositeAudioClip, ColorClip, CompositeVideoClip

class VideoStacker:
    def __init__(self, top_video_path, bottom_video_path, output_path):
        self.top_path = top_video_path
        self.bottom_path = bottom_video_path
        self.output_path = output_path
        
        # Default Settings
        self.target_width = 1080
        self.target_height = 1920
        self.resize_mode = "crop"
        self.duration_mode = "shortest"
        self.audio_mode = "mix"
        self.manual_duration = 10
        self.volume = 1.0
        
        # Start Time Offsets
        self.top_offset = 0
        self.bottom_offset = 0
        self.is_preview = False 

    def load_clips(self):
        """Loads video clips safely."""
        try:
            self.clip1 = VideoFileClip(self.top_path)
            self.clip2 = VideoFileClip(self.bottom_path)
            return True, "Videos loaded successfully."
        except Exception as e:
            return False, f"Error loading videos: {e}"

    def apply_offsets(self):
        """Cuts the beginning of the videos based on user offsets."""
        if self.top_offset > 0:
            self.clip1 = self.clip1.subclip(self.top_offset)
        if self.bottom_offset > 0:
            self.clip2 = self.clip2.subclip(self.bottom_offset)

    def process_duration(self):
        """Adjusts duration based on user preference."""
        d1 = self.clip1.duration
        d2 = self.clip2.duration

        # Preview Mode Limit
        if self.is_preview:
            preview_dur = min(5, d1, d2)
            self.clip1 = self.clip1.subclip(0, preview_dur)
            self.clip2 = self.clip2.subclip(0, preview_dur)
            return

        if self.duration_mode == "shortest":
            final_duration = min(d1, d2)
            self.clip1 = self.clip1.subclip(0, final_duration)
            self.clip2 = self.clip2.subclip(0, final_duration)
            
        elif self.duration_mode == "manual":
            final_duration = self.manual_duration
            
            # Loop or Cut Top
            if d1 < final_duration: 
                self.clip1 = self.clip1.loop(duration=final_duration)
            else: 
                self.clip1 = self.clip1.subclip(0, final_duration)
            
            # Loop or Cut Bottom
            if d2 < final_duration: 
                self.clip2 = self.clip2.loop(duration=final_duration)
            else: 
                self.clip2 = self.clip2.subclip(0, final_duration)

        elif self.duration_mode == "loop_shortest":
            final_duration = max(d1, d2)
            if d1 < final_duration: self.clip1 = self.clip1.loop(duration=final_duration)
            if d2 < final_duration: self.clip2 = self.clip2.loop(duration=final_duration)

    def resize_clip(self, clip, width, height):
        """Resizes a clip to fill half the screen."""
        if self.resize_mode == "stretch":
            return clip.resize(newsize=(width, height))
        
        elif self.resize_mode == "fit":
            # Resize to fit within box, keep aspect ratio
            if clip.w < clip.h:
                resized = clip.resize(width=width)
            else:
                resized = clip.resize(height=height)
                
            # Create black background
            bg = ColorClip(size=(width, height), color=(0,0,0), duration=clip.duration)
            
            # FIXED: Use CompositeVideoClip instead of .overlay()
            return CompositeVideoClip([bg, resized.set_position("center")])
            
        elif self.resize_mode == "crop":
            # Resize to fill strictly (Center Crop)
            w_ratio = width / clip.w
            h_ratio = height / clip.h
            scale = max(w_ratio, h_ratio)
            clip_resized = clip.resize(scale)
            return clip_resized.crop(width=width, height=height, x_center=clip_resized.w/2, y_center=clip_resized.h/2)

    def process_audio(self, final_clip):
        """Handles audio mixing logic."""
        if self.audio_mode == "mute":
            return final_clip.without_audio()
        
        audio1 = self.clip1.audio.volumex(self.volume) if self.clip1.audio else None
        audio2 = self.clip2.audio.volumex(self.volume) if self.clip2.audio else None

        if self.audio_mode == "top" and audio1:
            return final_clip.set_audio(audio1)
        elif self.audio_mode == "bottom" and audio2:
            return final_clip.set_audio(audio2)
        elif self.audio_mode == "mix":
            audios = [a for a in [audio1, audio2] if a is not None]
            if audios:
                mixed = CompositeAudioClip(audios)
                return final_clip.set_audio(mixed)
        
        return final_clip

    def render(self, progress_callback=None):
        """Main pipeline execution."""
        
        self.apply_offsets()
        self.process_duration()

        half_height = self.target_height // 2
        top_processed = self.resize_clip(self.clip1, self.target_width, half_height)
        bot_processed = self.resize_clip(self.clip2, self.target_width, half_height)

        final_video = clips_array([[top_processed], [bot_processed]])
        final_video = self.process_audio(final_video)

        final_video.write_videofile(
            self.output_path, 
            fps=30, 
            codec='libx264', 
            audio_codec='aac',
            preset='ultrafast' if self.is_preview else 'fast',
            threads=4,
            logger=progress_callback or 'bar'
        )
        
        self.clip1.close()
        self.clip2.close()
        return self.output_path