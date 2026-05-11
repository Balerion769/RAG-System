import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import {
  BarChart3,
  BrainCircuit,
  Camera,
  CheckCircle2,
  ExternalLink,
  FileText,
  Globe2,
  LucideAngularModule,
  Mic,
  Play,
  RefreshCcw,
  Send,
  ShieldCheck,
  Square,
  Upload,
  Video,
  XCircle
} from 'lucide-angular';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    importProvidersFrom(
      LucideAngularModule.pick({
        BarChart3,
        BrainCircuit,
        Camera,
        CheckCircle2,
        ExternalLink,
        FileText,
        Globe2,
        Mic,
        Play,
        RefreshCcw,
        Send,
        ShieldCheck,
        Square,
        Upload,
        Video,
        XCircle
      })
    )
  ]
};
