import { Hash, createHash } from "crypto";

export function sha1hash(s: string): string {
  const shasum: Hash = createHash("sha1");
  shasum.update(s);
  return shasum.digest("hex").substring(0, 8);
}
