import { CommonModule } from '@angular/common';
import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { firstValueFrom } from 'rxjs';

import {
  AnswerResponse,
  DocumentUploadResponse,
  EvidenceItem,
  ReportResponse,
  StartInterviewResponse,
  VerificationResponse
} from './models';
import { ApiService } from './services/api.service';

type UploadKind = 'resume' | 'job_description' | 'reference';

interface ChatItem {
  type: 'question' | 'answer' | 'feedback';
  text: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    LucideAngularModule
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  private readonly api = inject(ApiService);

  @ViewChild('preview') preview?: ElementRef<HTMLVideoElement>;

  roleTitle = 'AI/ML Engineer';
  focusSkills = 'Python, RAG, FastAPI, Angular';
  answer = '';
  status = 'Ready';
  error = '';

  resumeFile?: File;
  jdFile?: File;
  referenceFile?: File;
  resumeUpload?: DocumentUploadResponse;
  jdUpload?: DocumentUploadResponse;
  referenceUpload?: DocumentUploadResponse;

  session?: StartInterviewResponse;
  latestEvidence: EvidenceItem[] = [];
  report?: ReportResponse;
  chat: ChatItem[] = [];
  webVerification = true;
  latestVerification?: VerificationResponse;

  stream?: MediaStream;
  mediaRecorder?: MediaRecorder;
  recordedChunks: Blob[] = [];
  isCameraOn = false;
  isRecording = false;

  get canStartInterview(): boolean {
    return Boolean(this.resumeUpload || this.jdUpload || this.referenceUpload);
  }

  get scoreEntries(): Array<{ key: string; value: number }> {
    const scores = this.report?.overall_scores ?? {};
    return Object.entries(scores).map(([key, value]) => ({ key, value }));
  }

  selectFile(event: Event, kind: UploadKind): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    if (kind === 'resume') {
      this.resumeFile = file;
    } else if (kind === 'job_description') {
      this.jdFile = file;
    } else {
      this.referenceFile = file;
    }
  }

  async uploadSelected(kind: UploadKind): Promise<void> {
    const file = this.fileFor(kind);
    if (!file) {
      this.error = 'Choose a file first.';
      return;
    }

    this.status = 'Uploading';
    this.error = '';
    try {
      const response = await firstValueFrom(this.api.uploadDocument(file, kind));
      if (kind === 'resume') {
        this.resumeUpload = response;
      } else if (kind === 'job_description') {
        this.jdUpload = response;
      } else {
        this.referenceUpload = response;
      }
      this.status = 'Indexed';
    } catch (error) {
      this.handleError(error, 'Upload failed');
    }
  }

  async startInterview(): Promise<void> {
    if (!this.canStartInterview) {
      this.error = 'Upload at least one document.';
      return;
    }
    this.status = 'Starting';
    this.error = '';
    try {
      const focus_skills = this.focusSkills
        .split(',')
        .map((skill) => skill.trim())
        .filter(Boolean);
      this.session = await firstValueFrom(
        this.api.startInterview({
          role_title: this.roleTitle,
          resume_document_id: this.resumeUpload?.document_id,
          job_document_id: this.jdUpload?.document_id,
          focus_skills
        })
      );
      this.latestEvidence = this.session.evidence;
      this.chat = [{ type: 'question', text: this.session.question }];
      this.status = 'Interviewing';
      await this.refreshReport();
    } catch (error) {
      this.handleError(error, 'Could not start interview');
    }
  }

  async sendAnswer(): Promise<void> {
    const trimmed = this.answer.trim();
    if (!this.session || !trimmed) {
      return;
    }
    this.status = 'Scoring';
    this.error = '';
    this.chat.push({ type: 'answer', text: trimmed });
    this.answer = '';
    try {
      const response: AnswerResponse = await firstValueFrom(
        this.api.answer(this.session.session_id, trimmed, this.webVerification)
      );
      this.latestEvidence = response.evidence;
      this.latestVerification = response.verification ?? undefined;
      this.chat.push({ type: 'feedback', text: response.feedback });
      this.chat.push({ type: 'question', text: response.next_question });
      this.session = {
        session_id: response.session_id,
        question: response.next_question,
        evidence: response.evidence
      };
      await this.refreshReport();
      this.status = 'Interviewing';
    } catch (error) {
      this.handleError(error, 'Could not score answer');
    }
  }

  async verifyDraftAnswer(): Promise<void> {
    const trimmed = this.answer.trim();
    if (!trimmed) {
      this.error = 'Type an answer before verifying.';
      return;
    }
    this.status = 'Verifying';
    this.error = '';
    try {
      this.latestVerification = await firstValueFrom(
        this.api.verifyAnswer({
          answer: trimmed,
          question: this.session?.question,
          role_title: this.roleTitle,
          max_claims: 5
        })
      );
      this.status = 'Verified';
    } catch (error) {
      this.handleError(error, 'Web verification failed');
    }
  }

  async startCamera(): Promise<void> {
    this.error = '';
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      this.isCameraOn = true;
      queueMicrotask(() => {
        if (this.preview?.nativeElement && this.stream) {
          this.preview.nativeElement.srcObject = this.stream;
        }
      });
    } catch (error) {
      this.handleError(error, 'Camera permission failed');
    }
  }

  startRecording(): void {
    if (!this.stream) {
      this.error = 'Turn on camera first.';
      return;
    }
    this.recordedChunks = [];
    const mimeType = this.pickMimeType();
    this.mediaRecorder = mimeType
      ? new MediaRecorder(this.stream, { mimeType })
      : new MediaRecorder(this.stream);
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.recordedChunks.push(event.data);
      }
    };
    this.mediaRecorder.onstop = () => void this.uploadRecording();
    this.mediaRecorder.start();
    this.isRecording = true;
    this.status = 'Recording';
  }

  stopRecording(): void {
    this.mediaRecorder?.stop();
    this.isRecording = false;
    this.status = 'Saving video';
  }

  stopCamera(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = undefined;
    this.isCameraOn = false;
    this.isRecording = false;
  }

  async refreshReport(): Promise<void> {
    if (!this.session) {
      return;
    }
    this.report = await firstValueFrom(this.api.report(this.session.session_id));
  }

  private async uploadRecording(): Promise<void> {
    if (!this.session || this.recordedChunks.length === 0) {
      this.status = 'Interviewing';
      return;
    }
    const mimeType = this.pickMimeType();
    const blob = new Blob(this.recordedChunks, mimeType ? { type: mimeType } : undefined);
    try {
      await firstValueFrom(this.api.uploadVideo(this.session.session_id, blob));
      this.status = 'Video saved';
    } catch (error) {
      this.handleError(error, 'Video upload failed');
    }
  }

  private fileFor(kind: UploadKind): File | undefined {
    if (kind === 'resume') {
      return this.resumeFile;
    }
    if (kind === 'job_description') {
      return this.jdFile;
    }
    return this.referenceFile;
  }

  private pickMimeType(): string {
    if (MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus')) {
      return 'video/webm;codecs=vp9,opus';
    }
    if (MediaRecorder.isTypeSupported('video/webm')) {
      return 'video/webm';
    }
    return '';
  }

  private handleError(error: unknown, fallback: string): void {
    console.error(error);
    this.error = fallback;
    this.status = 'Needs attention';
  }

  verdictLabel(value: string | undefined): string {
    if (!value) {
      return 'not checked';
    }
    return value.replaceAll('_', ' ');
  }

  verdictClass(value: string | undefined): string {
    if (!value) {
      return 'neutral';
    }
    if (value === 'verified') {
      return 'verified';
    }
    if (value === 'partially_verified') {
      return 'partial';
    }
    if (value === 'needs_review') {
      return 'review';
    }
    return 'unverified';
  }
}
