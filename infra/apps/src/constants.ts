import { join } from "path";
import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

export const config = new pulumi.Config();
export const rootDir = join(__dirname, "..", "..", "..");
export const stackName = pulumi.getStack();
export const sslCertificate = pulumi.output(
  aws.acm.getCertificate({
    domain: "*.probablefutures.org",
    mostRecent: true,
  })
);
