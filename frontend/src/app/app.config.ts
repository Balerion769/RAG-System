import { ApplicationConfig, importProvidersFrom } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import {
  BarChart3,
  BrainCircuit,
  Camera,
  FileText,
  LucideAngularModule,
  Mic,
  Play,
  RefreshCcw,
  Send,
  Square,
  Upload,
  Video
} from 'lucide-angular';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    importProvidersFrom(
      LucideAngularModule.pick({
        BarChart3,
        BrainCircuit,
        Camera,
        FileText,
        Mic,
        Play,
        RefreshCcw,
        Send,
        Square,
        Upload,
        Video
      })
    )
  ]
};
