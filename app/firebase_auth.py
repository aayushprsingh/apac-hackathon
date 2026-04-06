"""
Firebase Auth Backend for Cortex — Optional
Firebase is ONLY needed for Google OAuth sign-in + Firestore persistence.
For demo + email/password mode, this module does nothing.

To enable Firebase:
1. Create a Firebase project at console.firebase.google.com
2. Enable Authentication (Google + Email/Password)
3. Create a service account: IAM → Service Accounts → Create Key → JSON
4. Upload the JSON to Cloud Run as a secret or mount it at /app/firebase-credentials.json
5. Set env var GOOGLE_APPLICATION_CREDENTIALS=/app/firebase-credentials.json
"""

# Firebase is disabled by default for zero-config deployment.
# Enable by providing service account credentials as described above.
firebase_initialized = False
_use_firebase = False  # Flag to check if Firebase should be used
fb = None
