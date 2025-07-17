// import React, { useState } from 'react';
// import { Box, Button, TextField, Typography, Alert } from '@mui/material';

// // Import generated types
// import { 
//   UserRegistrationRequest, 
//   UserRegistrationResponse 
// } from '../types/generated/users';
// import { 
//   TokenRefreshRequest, 
//   TokenRefreshResponse,
//   SSOAuthResponse 
// } from '../types/generated/auth';
// import { ProviderInfo } from '../types/generated/sso';

// /**
//  * Example component demonstrating usage of generated TypeScript interfaces
//  */
// const ExampleWithGeneratedTypes: React.FC = () => {
//   // Using generated types for state
//   const [registrationData, setRegistrationData] = useState<UserRegistrationRequest>({
//     username: '',
//     email: '',
//     password: '',
//     given_name: '',
//     family_name: '',
//     provider: 'keycloak',
//     send_verification_email: true,
//   });

//   const [providers, setProviders] = useState<ProviderInfo[]>([]);
//   const [authResponse, setAuthResponse] = useState<SSOAuthResponse | null>(null);

//   // Example function using generated types
//   const handleRegistration = async (data: UserRegistrationRequest): Promise<UserRegistrationResponse> => {
//     const response = await fetch('/auth/register', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(data),
//     });

//     if (!response.ok) {
//       throw new Error('Registration failed');
//     }

//     // TypeScript knows the exact shape of the response
//     const result: UserRegistrationResponse = await response.json();
//     return result;
//   };

//   // Example with token refresh
//   const refreshToken = async (refreshToken: string): Promise<TokenRefreshResponse> => {
//     const request: TokenRefreshRequest = {
//       refresh_token: refreshToken,
//       provider: 'keycloak',
//     };

//     const response = await fetch('/auth/refresh', {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(request),
//     });

//     const result: TokenRefreshResponse = await response.json();
    
//     // TypeScript provides autocomplete for all fields
//     console.log('New access token:', result.access_token);
//     console.log('Expires in:', result.expires_in);
    
//     return result;
//   };

//   // Example fetching providers
//   const fetchProviders = async () => {
//     const response = await fetch('/auth/providers');
//     const data: ProviderInfo[] = await response.json();
    
//     // TypeScript knows the exact shape of each provider
//     data.forEach(provider => {
//       console.log(`Provider: ${provider.name} (${provider.display_name})`);
//       console.log(`Type: ${provider.type}`);
//       console.log(`Enabled: ${provider.enabled}`);
//       if (provider.login_url) {
//         console.log(`Login URL: ${provider.login_url}`);
//       }
//     });

//     setProviders(data);
//   };

//   return (
//     <Box sx={{ p: 3 }}>
//       <Typography variant="h4" gutterBottom>
//         Example: Using Generated TypeScript Interfaces
//       </Typography>

//       <Alert severity="info" sx={{ mb: 3 }}>
//         This component demonstrates how to use the auto-generated TypeScript interfaces
//         from Pydantic models. All types are strongly typed with full IntelliSense support!
//       </Alert>

//       <Box sx={{ mb: 3 }}>
//         <Typography variant="h6" gutterBottom>
//           Registration Form (using UserRegistrationRequest)
//         </Typography>
        
//         <TextField
//           label="Username"
//           value={registrationData.username}
//           onChange={(e) => setRegistrationData(prev => ({
//             ...prev,
//             username: e.target.value
//           }))}
//           fullWidth
//           margin="normal"
//         />
        
//         <TextField
//           label="Email"
//           type="email"
//           value={registrationData.email}
//           onChange={(e) => setRegistrationData(prev => ({
//             ...prev,
//             email: e.target.value
//           }))}
//           fullWidth
//           margin="normal"
//         />

//         <Button 
//           variant="contained" 
//           onClick={() => handleRegistration(registrationData)}
//           sx={{ mt: 2 }}
//         >
//           Register User
//         </Button>
//       </Box>

//       <Box sx={{ mb: 3 }}>
//         <Typography variant="h6" gutterBottom>
//           Available Providers
//         </Typography>
        
//         <Button variant="outlined" onClick={fetchProviders}>
//           Fetch Providers
//         </Button>

//         {providers.length > 0 && (
//           <Box sx={{ mt: 2 }}>
//             {providers.map(provider => (
//               <Box key={provider.name} sx={{ p: 1, border: '1px solid #ddd', mb: 1 }}>
//                 <Typography>
//                   <strong>{provider.display_name}</strong> ({provider.name})
//                 </Typography>
//                 <Typography variant="body2">
//                   Type: {provider.type} | Enabled: {provider.enabled ? 'Yes' : 'No'}
//                 </Typography>
//               </Box>
//             ))}
//           </Box>
//         )}
//       </Box>

//       <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100' }}>
//         <Typography variant="body2">
//           <strong>Benefits of Generated Types:</strong>
//         </Typography>
//         <ul>
//           <li>Full IntelliSense and autocomplete in VS Code</li>
//           <li>Compile-time type checking</li>
//           <li>Always in sync with backend Pydantic models</li>
//           <li>No manual type definitions needed</li>
//           <li>Reduces runtime errors from API mismatches</li>
//         </ul>
//       </Box>
//     </Box>
//   );
// };

// export default ExampleWithGeneratedTypes;