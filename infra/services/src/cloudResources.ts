import * as aws from "@pulumi/aws";

import { config, vpc } from "./config";
import * as cloudfront from "./heplers/cloudfront";
import getSubdomain from "./heplers/getSubdomain";

const resource = `${config.stackName}-assistant`;
const subdomain = getSubdomain("chat");

const alb = new aws.lb.LoadBalancer(resource, {
  loadBalancerType: "application",
  securityGroups: [
    config.publicHttpSecurityGroupId,
    config.publicEgressSecurityGroupId,
  ],
  subnets: config.vpc.publicSubnetIds,
  accessLogs: {
    bucket: config.environmentLogsBucketId,
    enabled: true,
  },
  tags: config.createTags({
    name: `${config.stackName}-assistant-lb`,
    service: "core",
  }),
});

const cache = cloudfront.createDistribution(resource, {
  allowedMethods: ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
  cachedMethods: ["GET", "HEAD", "OPTIONS"],
  domainAlias: `${subdomain}.probablefutures.org`,
  forward: {
    cookies: { forward: "all" },
    headers: ["*"],
    queryString: true,
  },
  origin: {
    target: alb,
    type: "custom",
  },
  originReadTimeout: 60,
  tags: config.createTags({ name: `${resource}-cdn`, service: "core" }),
});

new aws.route53.Record(resource, {
  zoneId: config.route53ZoneId,
  name: subdomain,
  type: "A",
  aliases: [
    {
      name: cache.domainName,
      zoneId: cache.hostedZoneId,
      evaluateTargetHealth: true,
    },
  ],
});

export const assistantTargetGroup = new aws.lb.TargetGroup(resource, {
  healthCheck: { path: "/healthz" },
  protocol: "HTTP",
  port: config.api.port,
  vpcId: vpc.id,
  tags: config.createTags({ name: `${resource}-tg`, service: "core" }),
  targetType: "ip",
});

new aws.lb.Listener(`${resource}-http`, {
  loadBalancerArn: alb.arn,
  port: 80,
  defaultActions: [
    {
      redirect: {
        port: "443",
        protocol: "HTTPS",
        statusCode: "HTTP_301",
      },
      type: "redirect",
    },
  ],
  protocol: "HTTP",
});

new aws.lb.Listener(`${resource}-https`, {
  loadBalancerArn: alb.arn,
  certificateArn: config.ssl.usWest2.arn,
  sslPolicy: "ELBSecurityPolicy-2016-08",
  protocol: "HTTPS",
  port: 443,
  defaultActions: [
    {
      type: "forward",
      targetGroupArn: assistantTargetGroup.arn,
    },
  ],
});
