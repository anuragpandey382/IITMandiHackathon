import os
import torch
import logging
import numpy as np
import multiprocessing
from typing import List, Tuple
from pydub import AudioSegment
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)



# Constants
SAMPLING_RATE = 16000
lock = multiprocessing.Lock()
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(
        self,
        num_gpus: int = 1,
        min_duration_s: float = 0.5,
        max_duration_s: float = 15,
        sampling_rate: int = SAMPLING_RATE
    ):
        self.sampling_rate = sampling_rate
        self.min_duration_s = min_duration_s
        self.max_duration_s = max_duration_s
        self.num_gpus = num_gpus

    def is_supported_format(self, file_path: str) -> bool:
        """Check if the file format is supported."""
        supported_extensions = {'.wav', '.mp3', '.m4a', '.aac', '.ogg', '.wma'}
        _, ext = os.path.splitext(file_path)
        return ext.lower() in supported_extensions

    def get_speech_chunks(
        self,
        wav: torch.Tensor,
        model: torch.nn.Module,
        utils: tuple,
        silence_dur: int = 1000,
        device: str = "cuda"
    ) -> List[Tuple[int, int]]:
        """Get speech chunks using Silero VAD with recursive splitting for long segments."""
        get_speech_timestamps = utils[0]
        max_dur = self.max_duration_s * self.sampling_rate

        speech_timestamps = get_speech_timestamps(
            wav.to(device),
            model,
            sampling_rate=self.sampling_rate,
            min_silence_duration_ms=silence_dur,
            max_speech_duration_s=self.max_duration_s
        )

        final_timestamps = []
        for i in speech_timestamps:
            start = i["start"]
            end = i["end"]
            if end - start <= max_dur:
                final_timestamps.append((start, end))
            else:
                if silence_dur == 100:
                    final_timestamps.append((start, end))
                else:
                    new_stamps = self.get_speech_chunks(
                        wav[start:end],
                        model,
                        utils,
                        silence_dur - 100,
                        device=device
                    )
                    for j in new_stamps:
                        final_timestamps.append((start + j[0], start + j[1]))

        return final_timestamps

    def process_audio_segments(self, files: List[str], device: str):
        """Process audio segments using Silero VAD."""
        # Initialize Silero VAD model
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad"
        )
        model.to(device)
        
        _, _, read_audio, _, _ = utils

        progress_columns = (
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            TaskProgressColumn(),
            "Elapsed:",
            TimeElapsedColumn(),
            "Remaining:",
            TimeRemainingColumn(),
        )

        with Progress(*progress_columns) as progress_bar:
            task = progress_bar.add_task("[blue]Processing audio files...", total=len(files))

            for filename in files:
                try:
                    if not self.is_supported_format(filename):
                        logger.warning(f"Unsupported format: {filename}")
                        continue

                    basename = os.path.splitext(os.path.basename(filename))[0]
                    parent_dir = os.path.dirname(filename)

                    # Create output directory inside the parent directory
                    dest_dir = os.path.join(parent_dir, basename)
                    os.makedirs(dest_dir, exist_ok=True)

                    # Read audio using Silero's utility
                    wav = read_audio(filename, sampling_rate=self.sampling_rate)

                    # Get speech chunks
                    time_stamps = self.get_speech_chunks(
                        wav=wav,
                        model=model,
                        utils=utils,
                        silence_dur=1000,
                        device=device
                    )

                    # Load audio for segmentation
                    audio = AudioSegment.from_file(file=filename,format = filename.split('.')[-1])

                    chunks_created = 0
                    for n, (start, end) in enumerate(time_stamps):
                        time_st = (start / self.sampling_rate) * 1000
                        time_en = (end / self.sampling_rate) * 1000
                        duration = (time_en - time_st) / 1000

                        if duration < self.min_duration_s:
                            continue

                        chunk_path = os.path.join(
                            dest_dir,
                            f"{basename}_chunk_{str(n).zfill(5)}.flac"
                        )
                        
                        audio = audio.set_channels(1)
                        audio = audio.set_frame_rate(24000).set_sample_width(2)
                        segment = audio[time_st:time_en]
                        # Normalize the segment
                        segment = segment.normalize()
                        segment.export(chunk_path, format="flac")
                        chunks_created += 1

                    logger.info(f"Created {chunks_created} chunks from {filename}")

                    # Remove original file after successful chunking
                    os.remove(filename)
                    logger.info(f"Removed original file: {filename}")
                    #progress_bar.update(task, advance=1)

                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
                    try:
                        if os.path.exists(filename):
                           #os.remove(filename)
                           pass
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up {filename}: {str(cleanup_error)}")

                finally:
                    progress_bar.update(task, advance=1)

def process_audio_folder(
    input_path: str,
    num_gpus: int = 1,
    min_duration_s: float = 0.5,
    max_duration_s: float = 15
) -> None:
    """Process all audio files recursively in a folder using multiple GPUs."""
    # Initialize processor
    processor = AudioProcessor(
        num_gpus=num_gpus,
        min_duration_s=min_duration_s,
        max_duration_s=max_duration_s
    )

    # Recursively collect all audio files 
    audio_files1 = []
    for root, _, files in os.walk(input_path):
        for file in files:
            full_path = os.path.join(root, file)
            if processor.is_supported_format(full_path):
                audio_files1.append(full_path)
    
    audio_files = audio_files1
    # Split files among GPUs
    files_chunks = np.array_split(audio_files, num_gpus)
    process_chunks = []
    for file_chunk, gpu_id in zip(files_chunks, range(num_gpus)):
        process_chunks.append((file_chunk.tolist(), f"cuda:{gpu_id}"))

    # Create and start processes
    processes = []
    for i in range(num_gpus):
        process = multiprocessing.Process(
            target=processor.process_audio_segments,
            args=process_chunks[i]
        )
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()
    



if __name__ == "__main__":
    import argparse
    import time
    start=time.time()
    parser = argparse.ArgumentParser(description='Process audio files recursively using Silero VAD')
    parser.add_argument('--input_path', type=str, required=True,
                      help='Path to root folder containing audio files')
    parser.add_argument('--num_gpus', type=int, default=2,
                      help='Number of GPUs to use')
    parser.add_argument('--min_duration', type=float, default=0.5,
                      help='Minimum duration of segments in seconds')
    parser.add_argument('--max_duration', type=float, default=10,
                      help='Maximum duration of segments in seconds')                                                                                                                                                                                                   
    
    args = parser.parse_args()                                                                                                                                                                                                                                  
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    process_audio_folder(
        args.input_path,
        args.num_gpus,
        args.min_duration,
        args.max_duration
    )
    
    time_taken=time.time() - start
    print(f"time taken by gpu is {time_taken}")
