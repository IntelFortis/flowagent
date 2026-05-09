/**
 * Build default config values from a node definition's config array.
 */
export function buildDefaultConfig(configFields: any[]): Record<string, any> {
  const config: Record<string, any> = {}
  if (!configFields) return config
  for (const field of configFields) {
    if (field.default !== undefined && field.default !== '') {
      config[field.key] = field.default
    }
  }
  return config
}
