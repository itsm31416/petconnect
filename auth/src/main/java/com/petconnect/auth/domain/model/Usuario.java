package com.petconnect.auth.domain.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter

public class Usuario {
    private Long id;
    private String nombre;
    private String email;
    private String password;
    private String rol;
    private LocalDate fechaNacimiento;
    private String direccion;
}
