import * as pulumi from "@pulumi/pulumi";
import { Config as PulumiConfig } from "@pulumi/pulumi/config";
import * as aws from "@pulumi/aws";

enum RequiredTagKeys {
  Name = "Name",
  Environment = "Environment",
  Service = "Service",
  PulumiProject = "PulumiProject",
}

type RequiredTags = {
  [requiredTag in keyof typeof RequiredTagKeys]: string;
};

type Tags = RequiredTags & aws.Tags;

type CreateTagsArgs = {
  name: string;
  service: string;
  override?: Partial<Tags>;
};

export interface BaseConfig {
  pulumiConfig: PulumiConfig;
  projectName: string;
  stackName: string;
  createTags(args: CreateTagsArgs): Tags;
}

export const createBaseConfig = ({
  pulumiConfig = new PulumiConfig(),
  projectName = pulumi.getProject(),
  stackName = pulumi.getStack(),
}: Partial<BaseConfig> = {}): BaseConfig => ({
  pulumiConfig,
  projectName,
  stackName,
  createTags: ({ name, service, override }) => ({
    [RequiredTagKeys.Name]: name,
    [RequiredTagKeys.Service]: service,
    [RequiredTagKeys.Environment]: stackName,
    [RequiredTagKeys.PulumiProject]: projectName,
    ...(override ?? ({} as aws.Tags)),
  }),
});
