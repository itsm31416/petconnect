package com.petconnect.auth.domain.model.gateway;

import com.petconnect.auth.domain.model.Usuario;

public interface UsuarioGateway {

    Usuario guardarUsuario(Usuario usuario);
    void eliminarUsuario(Long id);
    Usuario buscarPorId(Long id);

}
