# Video walkthrough style

The goal is to teach people how to use the app, not to promote it.

## Format

| Item | Value |
|---|---|
| Resolution | 1920×1080 (16:9), like a Full HD monitor |
| Codec | H.264 `yuv420p`, `-crf 18`, 30 fps, `+faststart` |
| Source | 1920×1080 viewport at device scale 2 (3840×2160 real pixels). Zooms up to 2.2× stay sharp |
| Length | 1 to 5 minutes per video. Longer: split the walkthrough |
| Subtitles | `.srt` next to the MP4, with every step's caption |
| Music | None by default. With `--music`, a second file `video-music.mp4` (volume 0.25, looped if the video is longer, 1 s fade in and 2 s fade out) |

## Structure

1. **Cover** (4 s): optional logo, "Video walkthrough", app name, role and walkthrough title.
2. **Scene card** (2.4 s) whenever the scene changes.
3. **Steps.** Every step follows this sequence:
   - the camera pans and zooms to the element (1 s, ease-in-out), cross-fading
     from the previous screen;
   - the cursor moves to the element (on `click` and `type`);
   - the **red box** appears around the field or button;
   - the **caption** shows in a dark band with an accent border, with
     "Step N of M · Scene" and the bold words highlighted. It sits at the
     bottom, or at the top if it would cover the highlighted element;
   - reading pause: 2.6 to 8 s depending on the text length;
   - action: a red click pulse and a fade to the result, or text appearing in the field.
4. **Closing card** (4.5 s): optional logo, "End of walkthrough", app, role and support contact.

## Why frame by frame instead of a screencast

- Server wait times (AJAX, slow queries) never appear in the video.
- The result is deterministic. The same walkthrough produces the same video,
  and it is regenerated whenever the app changes.
- Zooming into a device-scale-2 screenshot stays sharp. A 1080p screencast
  zoomed in looks blurry.
- Captions and the cursor are drawn on a separate layer. They do not scale with the zoom.

## Lessons learned

- If the app looks wrong, the video will look wrong. Fix the app first.
- Always review the preview (`--preview`) before the full render.
- ffmpeg's `xfade` and `hstack` fail on mismatched inputs. That is why the
  compositing happens in an HTML page and ffmpeg only encodes.
- MP4 files are delivered outside the repository.
- Demos use fictitious or blurred data.
- Only use music you are licensed to use.
