const ciOnly = new Proxy(
  {},
  {
    get(_target, property) {
      if (property === 'then') return undefined;
      return (..._args: unknown[]) =>
        Promise.reject(
          new Error('CI-only AppDeploy client shim invoked at runtime. Use the real AppDeploy platform for SDK-backed execution.')
        );
    },
  }
) as any;

export const api = ciOnly;
export const auth = ciOnly;
export const image = ciOnly;
