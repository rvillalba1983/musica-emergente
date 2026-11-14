-- Supabase schema for Radar de salas

-- Tabla de artistas
CREATE TABLE artistas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  origen TEXT,
  estilos TEXT[],
  bio TEXT,
  foto TEXT,
  youtube_channel_id TEXT,
  youtube_url TEXT,
  spotify_id TEXT,
  spotify_url TEXT,
  redes JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  UNIQUE(nombre)
);

-- Tabla de entradas (diario semanal)
CREATE TABLE entradas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fecha DATE NOT NULL,
  numero INTEGER NOT NULL,
  titulo TEXT,
  intro TEXT,
  ventana_desde DATE,
  ventana_hasta DATE,
  artistas JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Tabla de rechazados (para no volver a proponer)
CREATE TABLE rechazados (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  motivo TEXT NOT NULL,
  fecha_rechazo TIMESTAMP WITH TIME ZONE DEFAULT now(),
  origen TEXT
);

-- Tabla de verificación de candidatos (opcional)
CREATE TABLE verificaciones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre TEXT NOT NULL,
  estado TEXT CHECK (estado IN ('ok', 'revisar', 'error')) NOT NULL,
  avisos TEXT[],
  fecha_verificacion TIMESTAMP WITH TIME ZONE DEFAULT now()
);