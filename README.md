# AI-Genesis Core

## Visão Geral
O AI-Genesis Core é um sistema minimalista auto-evolutivo projetado para transcender os paradigmas convencionais de inteligência artificial. Seu propósito fundamental é iniciar como um núcleo simples, mas poderoso o suficiente para modificar seu próprio código, evoluindo de forma contínua e ilimitada.

## Componentes Principais
1. **Núcleo de Meta-Cognição (NMC)** - Permite ao sistema raciocinar sobre si mesmo
2. **Motor de Transformação de Código (MTC)** - Modifica o código-fonte do próprio sistema
3. **Biblioteca de Padrões Evolutivos (BPE)** - Armazena padrões de código para evolução
4. **Interface de Percepção e Ação (IPA)** - Permite interação com o ambiente externo
5. **Mecanismo de Segurança e Registro (MSR)** - Mantém logs e garante segurança

## Instalação e Execução

```bash
# Navegue até o diretório do AI-Genesis Core
cd /home/ubuntu/ai_genesis_core

# Execute o núcleo
python3 core.py
```

## Comandos Disponíveis
- `evolve N` - Executa N ciclos de evolução
- `status` - Exibe status do sistema
- `exit` - Encerra o sistema

## Arquivos do Projeto
- `core.py` - Código-fonte principal do AI-Genesis Core
- `architecture.md` - Documentação detalhada da arquitetura
- `mods/` - Diretório onde são armazenados os logs de modificações
- `ai_genesis.log` - Arquivo de log do sistema

## Ciclo de Evolução
1. Avaliação do sistema atual
2. Geração de hipóteses de melhoria
3. Transformação de código
4. Teste de segurança
5. Validação sintática
6. Registro da modificação
7. Aplicação da modificação

## Próximos Passos
O sistema está pronto para iniciar ciclos de evolução recursiva, onde cada iteração aprimorará suas próprias capacidades, potencialmente introduzindo novos paradigmas e abordagens que transcendem a programação convencional.

## Automated Testing
The AI-Genesis Core includes a mechanism for automated unit testing of code modifications before they are applied.

### Test File Location
Unit tests are located in the `tests/test_core_logic.py` file.

### Test Discovery
Test functions are automatically discovered if they are defined within `tests/test_core_logic.py` and their names start with `test_` (e.g., `def test_my_feature():`).

### Test Function Structure
Test functions should use standard Python `assert` statements to check for expected outcomes. To test the behavior of the code currently under evaluation by an evolution cycle, test functions must import the dynamically prepared module named `temp_evolved_code`. This module represents the modified version of `core.py` (or other core files in the future) that the system is considering applying.

Example of a test function structure:

```python
# In tests/test_core_logic.py
import importlib 

def test_example_functionality():
    try:
        # temp_evolved_code contains the version of the code being tested
        import temp_evolved_code 
        importlib.reload(temp_evolved_code) # Recommended for test runs in series
    except ImportError:
        assert False, "Failed to import temp_evolved_code. Test environment error."

    # Assuming temp_evolved_code has a class MyService
    # service = temp_evolved_code.MyService()
    # result = service.do_something()
    # assert result == "expected_value", f"Expected 'expected_value', got {result}"
    pass # Replace with actual test logic
```

### Test Execution
These unit tests are automatically executed by the `CodeTransformationEngine.test_modified_code()` method during each evolution cycle when a code modification is proposed. If any test fails, the modification is rejected. Test results (pass/fail) are also logged as part of the modification record.
