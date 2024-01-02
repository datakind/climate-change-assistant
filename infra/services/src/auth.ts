import * as auth0 from "@pulumi/auth0";

import { config } from "./config";
import getSubdomain from "./heplers/getSubdomain";

// auth client for api access
const assistantApiAuth = new auth0.Client("AssistantApiAccess", {
  appType: "non_interactive",
  description: "Api Access for the AI Assistant",
  jwtConfiguration: {
    alg: "RS256",
    lifetimeInSeconds: 36000, // 10 hours
  },
  oidcConformant: true,
  grantTypes: ["client_credentials"],
  name: "Api Access for the AI Assistant",
});

const apiClientCredentials = new auth0.ClientCredentials(
  "assistant-api-client-credentials",
  {
    clientId: assistantApiAuth.clientId,
    authenticationMethod: "client_secret_post",
  }
);

// spa client for user authentication
const assistantAuth = new auth0.Client("Assistant", {
  appType: "spa",
  description: "Probable Futures Assistant",
  jwtConfiguration: {
    alg: "RS256",
    lifetimeInSeconds: 36000, // 10 hours
  },
  refreshToken: {
    expirationType: "expiring",
    rotationType: "rotating",
    idleTokenLifetime: 1296000, // 15 days
  },
  oidcConformant: true,
  grantTypes: ["authorization_code", "refresh_token"],
  allowedLogoutUrls: [`https://${getSubdomain("chat")}.probablefutures.org`],
  callbacks: [
    `http://${getSubdomain(
      "chat"
    )}.probablefutures.org/auth/oauth/auth0/callback`,
  ],
  webOrigins: [`https://${getSubdomain("chat")}.probablefutures.org/`],
  name: "Probable Futures Assistant",
  logoUri:
    "https://user-images.githubusercontent.com/894075/101797194-be4c8e80-3ad7-11eb-86c8-82516c0a96f0.png",
  tokenEndpointAuthMethod: "none",
});

const clientCredentials = new auth0.ClientCredentials(
  "assistant-client-credentials",
  {
    clientId: assistantAuth.clientId,
    authenticationMethod: "client_secret_post",
  }
);

new auth0.ConnectionClient("google-conn-assistant-client-association", {
  connectionId: config.auth0.googleConnectionId,
  clientId: assistantAuth.clientId,
});

const assistantUserDb = new auth0.Connection("assitant-user-db", {
  options: {
    disableSignup: true,
  },
  strategy: "auth0",
});

new auth0.ConnectionClient("useDb-conn-assistant-client-association", {
  connectionId: assistantUserDb.id,
  clientId: assistantAuth.clientId,
});

export const assistantAuthClientId = assistantAuth.clientId;
export const assistantAuthClientSecret = clientCredentials.clientSecret;

export const assistantApiAuthClientId = assistantApiAuth.clientId;
export const assistantApiAuthClientSecret = apiClientCredentials.clientSecret;
