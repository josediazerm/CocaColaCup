#===============================================================================
# Auto-Save System (portado desde POKEMON Z V2.05)
#-------------------------------------------------------------------------------
# - Guarda la partida automáticamente cada SAVE_INTERVAL_SECONDS segundos
#   mientras se está en el overworld (Scene_Map).
# - Cada BACKUP_INTERVAL_SECONDS segundos crea una copia con marca de tiempo
#   del archivo de guardado actual y mantiene únicamente las BACKUP_KEEP_COUNT
#   copias más recientes.
# - Siempre activado. No se puede desactivar desde el menú.
#-------------------------------------------------------------------------------
# Equivalente moderno (Essentials v19+) del bloque "AUTOSAVE + ZIP BACKUP"
# de POKEMON Z (107_PField_EncounterModifiers.rb). Reemplaza el monkeypatch
# directo de Scene_Map#update por un EventHandler en :on_frame_update y la
# llamada a PowerShell por una rotación de copias multiplataforma.
#===============================================================================

module AutoSave
  # Tiempo entre guardados automáticos.
  SAVE_INTERVAL_SECONDS   = 3
  # Tiempo entre copias de seguridad rotatorias.
  BACKUP_INTERVAL_SECONDS = 5 * 60
  # Número máximo de copias de seguridad conservadas.
  BACKUP_KEEP_COUNT       = 5
  # Prefijo de los archivos de respaldo.
  BACKUP_PREFIX           = "Game_backup_"
  BACKUP_SUFFIX           = ".rxdata"

  @last_save_frame   = 0
  @last_backup_frame = 0

  class << self
    attr_accessor :last_save_frame, :last_backup_frame

    # Convierte segundos a frames usando el frame_rate actual.
    def seconds_to_frames(secs)
      [(secs * Graphics.frame_rate).to_i, 1].max
    end

    # ¿Es seguro guardar ahora mismo?
    def ready_for_save?
      return false if !defined?($player) || $player.nil?
      return false if !defined?($scene)  || !$scene.is_a?(Scene_Map)
      return false if !defined?($game_temp) || $game_temp.nil?
      return false if $game_temp.player_transferring
      return false if $game_temp.transition_processing
      return false if $game_temp.message_window_showing
      return false if $game_temp.in_menu rescue false
      return true
    end

    # Punto de entrada llamado una vez por frame durante el overworld.
    def update
      return if !ready_for_save?
      now = Graphics.frame_count
      if now - @last_save_frame >= seconds_to_frames(SAVE_INTERVAL_SECONDS)
        do_save
        @last_save_frame = now
      end
      if now - @last_backup_frame >= seconds_to_frames(BACKUP_INTERVAL_SECONDS)
        do_backup
        @last_backup_frame = now
      end
    end

    # Guarda silenciosamente usando el API moderno (Essentials v19+).
    def do_save
      begin
        Game.save(SaveData::FILE_PATH, safe: false)
      rescue Exception => e
        echoln "[AutoSave] Falló el guardado automático: #{e.class}: #{e.message}" rescue nil
      end
    end

    # Crea una copia con marca de tiempo del archivo de guardado actual y rota
    # las antiguas para no acumular más de BACKUP_KEEP_COUNT.
    def do_backup
      begin
        return if !File.file?(SaveData::FILE_PATH)
        save_dir    = File.dirname(SaveData::FILE_PATH)
        timestamp   = Time.now.strftime("%Y%m%d_%H%M%S")
        backup_path = File.join(save_dir, "#{BACKUP_PREFIX}#{timestamp}#{BACKUP_SUFFIX}")
        File.open(SaveData::FILE_PATH, "rb") do |src|
          File.open(backup_path, "wb") do |dst|
            while (chunk = src.read(8192))
              dst.write(chunk)
            end
          end
        end
        rotate_backups(save_dir)
      rescue Exception => e
        echoln "[AutoSave] Falló la copia de seguridad: #{e.class}: #{e.message}" rescue nil
      end
    end

    # Mantiene únicamente las BACKUP_KEEP_COUNT copias más recientes.
    def rotate_backups(save_dir)
      pattern = File.join(save_dir, "#{BACKUP_PREFIX}*#{BACKUP_SUFFIX}")
      files = Dir.glob(pattern)
      return if files.length <= BACKUP_KEEP_COUNT
      sorted = files.sort_by { |f| File.mtime(f) rescue Time.at(0) }.reverse
      to_delete = sorted[BACKUP_KEEP_COUNT..-1] || []
      to_delete.each { |f| File.delete(f) rescue nil }
    end

    # Reinicia los contadores. Llamado cuando se carga una partida o se entra
    # en un mapa nuevo, para evitar un guardado inmediato tras la transición.
    def reset
      @last_save_frame   = Graphics.frame_count
      @last_backup_frame = Graphics.frame_count
    end
  end
end

#-------------------------------------------------------------------------------
# Hooks
#-------------------------------------------------------------------------------
# Tick por frame durante el overworld.
EventHandlers.add(:on_frame_update, :auto_save_tick,
  proc { AutoSave.update }
)

# Reinicia los contadores cuando se entra en un mapa nuevo (tras carga,
# transferencia, salir de batalla, etc.) para no guardar de inmediato.
EventHandlers.add(:on_enter_map, :auto_save_reset,
  proc { |_old_map_id| AutoSave.reset }
)
