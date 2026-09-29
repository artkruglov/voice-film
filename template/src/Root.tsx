import { Composition } from "remotion";
import { Film } from "./film/Film";
import { DURATION } from "./film/cues";

type Props = { fps: number; vertical: boolean };
const meta = ({ props }: { props: Props }) => ({ fps: props.fps, durationInFrames: Math.max(1, Math.round(DURATION * props.fps)) });

/** One timeline, two formats. Audio is not in the composition: scripts/mix.py builds out/mix.wav and render.sh muxes it. */
export const Root = () => (
  <>
    <Composition id="Film" component={Film} width={1920} height={1080} fps={30} durationInFrames={Math.max(1, Math.round(DURATION * 30))} defaultProps={{ fps: 30, vertical: false }} calculateMetadata={meta} />
    <Composition id="FilmVertical" component={Film} width={1080} height={1920} fps={30} durationInFrames={Math.max(1, Math.round(DURATION * 30))} defaultProps={{ fps: 30, vertical: true }} calculateMetadata={meta} />
  </>
);
