import React, { useEffect, useMemo, useRef } from "react";

type FadeDirection = "in" | "out";

const VIDEO_URL =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260329_050842_be71947f-f16e-4a14-810c-06e83d23ddb5.mp4";

function clamp01(v: number) {
  return Math.max(0, Math.min(1, v));
}

export function VideoBackground() {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const rafIdRef = useRef<number | null>(null);
  const fadeStartTsRef = useRef<number | null>(null);
  const fadeFromRef = useRef<number>(0);
  const fadeToRef = useRef<number>(1);
  const fadingOutRef = useRef<boolean>(false);

  const style = useMemo<React.CSSProperties>(
    () => ({
      position: "absolute",
      inset: 0,
      width: "115%",
      height: "115%",
      left: "50%",
      top: 0,
      transform: "translateX(-50%)",
      objectFit: "cover",
      objectPosition: "top center",
      opacity: 0,
      pointerEvents: "none",
    }),
    [],
  );

  function cancelFade() {
    if (rafIdRef.current != null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
    fadeStartTsRef.current = null;
  }

  function setOpacity(op: number) {
    const video = videoRef.current;
    if (!video) return;
    video.style.opacity = String(clamp01(op));
  }

  function getOpacity(): number {
    const video = videoRef.current;
    if (!video) return 0;
    const parsed = Number.parseFloat(video.style.opacity || "0");
    return Number.isFinite(parsed) ? clamp01(parsed) : 0;
  }

  function startFade(direction: FadeDirection) {
    cancelFade();
    fadeFromRef.current = getOpacity();
    fadeToRef.current = direction === "in" ? 1 : 0;
    fadeStartTsRef.current = null;

    const durationMs = 250;

    const tick = (ts: number) => {
      if (fadeStartTsRef.current == null) fadeStartTsRef.current = ts;
      const elapsed = ts - fadeStartTsRef.current;
      const t = clamp01(elapsed / durationMs);
      const value = fadeFromRef.current + (fadeToRef.current - fadeFromRef.current) * t;
      setOpacity(value);

      if (t < 1) {
        rafIdRef.current = requestAnimationFrame(tick);
      } else {
        rafIdRef.current = null;
      }
    };

    rafIdRef.current = requestAnimationFrame(tick);
  }

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => {
      setOpacity(0);
      fadingOutRef.current = false;
      startFade("in");
    };

    const onTimeUpdate = () => {
      const duration = video.duration;
      if (!Number.isFinite(duration) || duration <= 0) return;

      const remaining = duration - video.currentTime;
      if (remaining <= 0.55 && !fadingOutRef.current) {
        fadingOutRef.current = true;
        startFade("out");
      }
    };

    const onEnded = () => {
      cancelFade();
      setOpacity(0);

      window.setTimeout(() => {
        try {
          video.currentTime = 0;
        } catch {
          // ignore
        }
        fadingOutRef.current = false;
        void video.play();
        startFade("in");
      }, 100);
    };

    video.addEventListener("loadeddata", onLoaded);
    video.addEventListener("timeupdate", onTimeUpdate);
    video.addEventListener("ended", onEnded);

    return () => {
      cancelFade();
      video.removeEventListener("loadeddata", onLoaded);
      video.removeEventListener("timeupdate", onTimeUpdate);
      video.removeEventListener("ended", onEnded);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <video
      ref={videoRef}
      src={VIDEO_URL}
      style={style}
      muted
      playsInline
      autoPlay
      loop={false}
      preload="auto"
    />
  );
}

