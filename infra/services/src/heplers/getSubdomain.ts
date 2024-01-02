import { config } from "../config";

const { stackName } = config;
export default function getSubdomain(resourceName?: string): string {
  let prefix: string;

  switch (stackName) {
    case "development": {
      prefix = "dev";
      break;
    }
    case "production": {
      prefix = "";
      break;
    }
    case "staging": {
      prefix = "staging";
      break;
    }
    default: {
      prefix = stackName;
      break;
    }
  }

  if (prefix && resourceName) {
    return `${prefix}-${resourceName}`;
  }

  if (resourceName) {
    return resourceName;
  }

  return prefix;
}
