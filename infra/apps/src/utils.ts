import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

import { sha1hash } from "./hash";

export const defaultTaskRolePolicyARNs = [
  // Provides wide access to "serverless" services (Dynamo, S3, etc.)
  aws.iam.ManagedPolicy.LambdaFullAccess,
  // Required for lambda compute to be able to run Tasks
  aws.iam.ManagedPolicy.AmazonECSFullAccess,
];

export const defaultExecutionRolePolicyARNs = [
  "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
];

export const defaultRoleAssumeRolePolicy: aws.iam.PolicyDocument = {
  Version: "2012-10-17",
  Statement: [
    {
      Action: "sts:AssumeRole",
      Principal: {
        Service: "ecs-tasks.amazonaws.com",
      },
      Effect: "Allow",
      Sid: "",
    },
  ],
};

export function createRoleAndPolicies(
  name: string,
  assumeRolePolicy: string | aws.iam.PolicyDocument,
  policyArns: string[],
  opts?: pulumi.ComponentResourceOptions | undefined
) {
  if (typeof assumeRolePolicy !== "string") {
    assumeRolePolicy = JSON.stringify(assumeRolePolicy);
  }

  const role = new aws.iam.Role(name, { assumeRolePolicy }, opts);
  const policies: aws.iam.RolePolicyAttachment[] = [];

  for (let i = 0; i < policyArns.length; i++) {
    const policyArn = policyArns[i];
    policies.push(
      new aws.iam.RolePolicyAttachment(
        `${name}-${sha1hash(policyArn)}`,
        { role, policyArn },
        opts
      )
    );
  }

  return { role, policies };
}

export function createDefaultECSRoles(name: string) {
  const task = createRoleAndPolicies(
    `${name}-task`,
    defaultRoleAssumeRolePolicy,
    defaultTaskRolePolicyARNs
  );

  const execution = createRoleAndPolicies(
    `${name}-execution`,
    defaultRoleAssumeRolePolicy,
    defaultExecutionRolePolicyARNs
  );
  return { task, execution };
}
