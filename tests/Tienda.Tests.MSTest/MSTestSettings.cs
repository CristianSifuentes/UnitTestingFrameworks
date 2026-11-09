// Paralelismo a nivel de método para todo el ensamblado (MSTest es secuencial por defecto).
[assembly: Parallelize(Scope = ExecutionScope.MethodLevel)]
