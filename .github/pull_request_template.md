## 📝 Descrição

<!-- Descreva brevemente as mudanças feitas neste PR -->

## 🎯 Tipo de Mudança

<!-- Marque a opção correspondente com [X] -->

- [ ] 🐛 Bug fix (correção de bug sem breaking changes)
- [ ] ✨ Feature (nova funcionalidade)
- [ ] 📚 Docs (mudanças apenas em documentação)
- [ ] 🔧 Chore (dependências, CI/CD, configs)
- [ ] ♻️ Refactor (código refatorado sem mudança de funcionalidade)
- [ ] 🚀 Performance (melhorias de performance)

## ✅ Checklist

### Obrigatório
- [ ] Nenhuma credencial ou secret hardcoded no código (`MONGO_URI`, `GEMINI_API_KEY`, etc.)
- [ ] Novas variáveis de ambiente foram adicionadas ao `settings.py` e validadas em `Settings.validate()`
- [ ] `requirements.txt` atualizado caso dependências tenham sido adicionadas ou alteradas
- [ ] Linter passou sem erros (`ruff check .` — recomendado: `pip install ruff`)
- [ ] Tipos estão corretos (`mypy src/` — recomendado: `pip install mypy`)
- [ ] Não há `print` de debug desnecessário (prints de log intencional são permitidos)
- [ ] Funções/classes novas possuem docstrings explicando propósito e argumentos
- [ ] Testei alterações localmente

## 📸 Screenshots (se aplicável)

<!-- Anexe screenshots para mudanças visuais -->

## 📋 Notas adicionais

<!-- Adicione qualquer contexto importante para os reviewers -->