import { adminToken, ADMIN_PASSWORD } from './flows/helpers.js';

/**
 * The default administrator password is temporary: the app asks for a new one before it loads.
 * This helper replaces it through the API (once) and returns the password that the login form needs.
 */
export async function adminPassword(page) {
  await adminToken(page.request);
  return ADMIN_PASSWORD;
}
