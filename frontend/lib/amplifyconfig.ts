import { Amplify } from "aws-amplify";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
      loginWith: {
        oauth: {
          domain: process.env.NEXT_PUBLIC_COGNITO_DOMAIN!,
          scopes: ["email", "openid", "profile"],
          redirectSignIn: ["http://localhost:3000/studio", "https://www.campaign.ongspace.com/studio"],
          redirectSignOut: ["http://localhost:3000/", "https://www.campaign.ongspace.com/"],
          responseType: "code",
        },
      },
    },
  },
}, { ssr: true });
