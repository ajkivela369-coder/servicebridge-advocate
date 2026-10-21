// JavaScript runtime example: TypeScript eventually becomes JavaScript like this.
export async function loadCases(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}
