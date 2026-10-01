import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VideoPlayer, VideoPlayerProps } from "./VideoPlayer";

describe("VideoPlayer", () => {
  const mockProps: VideoPlayerProps = {
    src: "https://test.com/video.mp4",
    title: "Clase de prueba",
  };

  it("renders the video element", () => {
    render(<VideoPlayer {...mockProps} />);
    const video = screen.getByTestId("video-element");
    expect(video).toBeInTheDocument();
  });

  it("renders the correct video source", () => {
    render(<VideoPlayer {...mockProps} />);
    const source = screen.getByTestId("video-element").querySelector("source");
    expect(source).toHaveAttribute("src", mockProps.src);
  });

  it("renders the title as fallback text", () => {
    render(<VideoPlayer {...mockProps} />);
    expect(screen.getByText(mockProps.title)).toBeInTheDocument();
  });

  it("embeds YouTube links in an iframe", () => {
    render(<VideoPlayer src="https://www.youtube.com/watch?v=dQw4w9WgXcQ" title="Clase de prueba" />);
    expect(screen.getByTestId("video-embed")).toHaveAttribute("src", "https://www.youtube.com/embed/dQw4w9WgXcQ");
    expect(screen.queryByTestId("video-element")).not.toBeInTheDocument();
  });
});
