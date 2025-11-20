import { Amplify } from "aws-amplify";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
      loginWith: {
        oauth: {
          domain: process.env.NEXT_PUBLIC_COGNITO_DOMAIN!,
          scopes: ["email", "openid"],
          redirectSignIn: ["http://localhost:3000/studio", "https://main.d1hfq20su6zuqk.amplifyapp.com/studio"],
          redirectSignOut: ["http://localhost:3000/", "https://main.d1hfq20su6zuqk.amplifyapp.com/"],
          responseType: "code",
        },
      },
    },
  },
}, { ssr: true });
