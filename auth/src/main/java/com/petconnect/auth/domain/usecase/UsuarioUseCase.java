package com.petconnect.auth.domain.usecase;


import com.petconnect.auth.domain.model.Usuario;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor


public class UsuarioUseCase {

    public Usuario guardarUsuario (Usuario usuario){

        if (usuario.getNombre()==null){
            throw new NullPointerException("El nombre del Usuario nulo");
        }

    }

}
