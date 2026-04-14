export const msalConfig = {
    auth: {
        // TODO: Replace this with your actual Azure Application Client ID
        clientId: "cddfb3f6-2167-45c1-84b2-e2db196c9600",

        // Use "common" for multi-tenant, or paste your specific Tenant ID below:
        authority: "https://login.microsoftonline.com/3dcd35b5-f9c5-48ca-8653-821568ad3397",

        // This must match exactly what you input in the Azure AD Portal
        redirectUri: "http://localhost:5173/",
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

export const loginRequest = {
    // These are the specific Graph API Scopes we request on behalf of the user
    scopes: ["User.Read", "Sites.Read.All", "Files.Read.All"]
};
