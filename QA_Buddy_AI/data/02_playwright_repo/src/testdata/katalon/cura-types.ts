export interface CuraUser {
    username: string;
    password: string;
}

export interface CuraInvalidUser {
    username: string;
    password: string;
    expectedError: string;
}

export interface CuraAppointmentData {
    facility: string;
    readmission: boolean;
    program: 'Medicare' | 'Medicaid' | 'None';
    visitDate: string;
    comment: string;
}

export interface CuraTestData {
    validUser: CuraUser;
    invalidUsers: CuraInvalidUser[];
    facilities: string[];
    healthcarePrograms: string[];
    defaultAppointment: CuraAppointmentData;
}
