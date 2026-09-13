usuario decidió: trabajar en el repo original (que tiene todo) y que yo haga push de lo que pueda en main, y PR+merge de mi branch si es verde. No instalar si rompe main. Ignorar scripts.

Decisión: 
1. Verificar estado actual: branch, archivos modificados, qué está tracked/untracked.
2. Si seed data/ está untracked (gitignore'd): no puedo pusharlo tal cual — decido si lo muevo a fixtures/ (tracked) o lo dejo local.
3. Si hay archivos tracked modificados/over new en mi branch: commit + push branch + PR; si pasa tests y tú apruebas → merge a main.
4. Si hay algo trackeado que rompería main al instalarme en ella (pip install cosas nuevas, cambios de dependencia, cambios estructurales sin tests): no lo forwardizo.

Entiendo que scripts se quitarán — no los toco ni los commito.
