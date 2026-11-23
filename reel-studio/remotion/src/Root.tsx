import { Composition } from "remotion";
import { FPS, H, W } from "./camera";
import { data, Reel } from "./Reel";

const total = Math.max(1, Math.round(data.duration * FPS));
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={total} fps={FPS} width={W} height={H} />
    {/* checkpoint: the first ~10 s, sent for approval before the full render */}
    <Composition id="Part1" component={Reel} durationInFrames={Math.min(total, 10 * FPS)} fps={FPS} width={W} height={H} />
  </>
);
