import { FC } from "react";
import styles from "./VideoPlayer.module.scss";

export interface VideoPlayerProps {
  src: string;
  title: string;
}

// Returns the embed URL for YouTube links (watch?v=, youtu.be/), or null for any other source
const getYouTubeEmbedUrl = (src: string): string | null => {
  const match = src.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})/);
  return match ? `https://www.youtube.com/embed/${match[1]}` : null;
};

export const VideoPlayer: FC<VideoPlayerProps> = ({ src, title }) => {
  const embedUrl = getYouTubeEmbedUrl(src);

  return (
    <div className={styles.videoPlayer}>
      {embedUrl ? (
        <iframe
          src={embedUrl}
          title={title}
          className={styles.video}
          data-testid="video-embed"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      ) : (
        <video controls className={styles.video} data-testid="video-element">
          <source src={src} type="video/mp4" />
          {title}
        </video>
      )}
    </div>
  );
};
