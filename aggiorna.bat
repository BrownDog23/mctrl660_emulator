@echo off
		echo ==========================================
		echo    SINCRONIZZAZIONE REPOSITORY GITHUB
		echo ==========================================
		echo.

		echo [1/3] Aggiunta file modificati...
		git add -A

		echo [2/3] Apertura Notepad++ per il messaggio di commit...
		echo (Salva e chiudi Notepad++ per continuare)
		git commit

		echo [3/3] Invio dei file al server (branch main)...
		git push origin main

		echo.
		echo ==========================================
		echo    OPERAZIONE COMPLETATA!
		echo    Premi un tasto per chiudere la finestra.
		echo ==========================================
		pause