import { Amplify } from "aws-amplify";

const local_domain = "http://localhost:3000";

const environment = process.env.NEXT_PUBLIC_APP_ENV;
const prod_domain = process.env.NEXT_PUBLIC_APP_DOMAIN;

let baseDomain: string;
if (environment === "prod" && prod_domain) {
  baseDomain = prod_domain;
} else {
  baseDomain = local_domain;
}

const redirectSignInUrls = [
  `${baseDomain}/studio`,
];

const redirectSignOutUrls = [
  `${baseDomain}/`,
];

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
      loginWith: {
        oauth: {
          domain: process.env.NEXT_PUBLIC_COGNITO_DOMAIN!,
          scopes: ["email", "openid", "profile"],
          redirectSignIn: redirectSignInUrls,
          redirectSignOut: redirectSignOutUrls,
          responseType: "code",
        },
      },
    },
  },
}, { ssr: true });
