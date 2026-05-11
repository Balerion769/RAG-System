import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  AnswerResponse,
  DocumentUploadResponse,
  ReportResponse,
  StartInterviewResponse,
  VerificationResponse,
  VideoUploadResponse
} from '../models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://127.0.0.1:8000';

  uploadDocument(file: File, sourceType: string): Observable<DocumentUploadResponse> {
    const body = new FormData();
    body.append('file', file);
    body.append('source_type', sourceType);
    return this.http.post<DocumentUploadResponse>(`${this.baseUrl}/documents/upload`, body);
  }

  startInterview(payload: {
    role_title: string;
    resume_document_id?: string;
    job_document_id?: string;
    focus_skills: string[];
  }): Observable<StartInterviewResponse> {
    return this.http.post<StartInterviewResponse>(`${this.baseUrl}/interviews/start`, payload);
  }

  answer(sessionId: string, answer: string, webVerification = false): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.baseUrl}/interviews/${sessionId}/answer`, {
      answer,
      web_verification: webVerification
    });
  }

  uploadVideo(sessionId: string, file: Blob, filename = 'interview.webm'): Observable<VideoUploadResponse> {
    const body = new FormData();
    body.append('file', file, filename);
    return this.http.post<VideoUploadResponse>(`${this.baseUrl}/interviews/${sessionId}/video`, body);
  }

  report(sessionId: string): Observable<ReportResponse> {
    return this.http.get<ReportResponse>(`${this.baseUrl}/interviews/${sessionId}/report`);
  }

  verifyAnswer(payload: {
    answer: string;
    question?: string;
    role_title?: string;
    max_claims?: number;
  }): Observable<VerificationResponse> {
    return this.http.post<VerificationResponse>(`${this.baseUrl}/verification/check`, payload);
  }
}
