-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 15-09-2025 a las 00:46:28
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `bd_empresa`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categoria`
--

CREATE TABLE `categoria` (
  `idcategoria` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(256) DEFAULT NULL,
  `estado` bit(1) DEFAULT b'1',
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_modifico` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `categoria`
--

INSERT INTO `categoria` (`idcategoria`, `nombre`, `descripcion`, `estado`, `fecha_creacion`, `fecha_modificacion`, `usuario_modifico`) VALUES
(1, 'Uniformes', 'Ropas escolares, institucionales y para deportes', b'1', '2025-09-06 18:04:27', '2025-09-06 18:04:27', 1),
(2, 'Ropa Casual', 'Prendas para uso diario y casual', b'1', '2025-09-06 18:04:27', '2025-09-06 18:04:27', 1),
(3, 'Ropa Industrial', 'Prendas para uso diario de trabajo', b'1', '2025-09-06 18:04:27', '2025-09-06 18:04:27', 1),
(4, 'Implementos Deportivos', 'Balones, conos, redes y otros accesorios', b'1', '2025-09-06 18:04:27', '2025-09-06 18:04:27', 1),
(5, 'Accesorios y Complemento Deportivos', 'Medias para deportes y entrenamiento', b'1', '2025-09-06 18:04:27', '2025-09-06 18:04:27', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cliente`
--

CREATE TABLE `cliente` (
  `idcliente` int(11) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `idtipodoc` int(11) NOT NULL,
  `num_documento` varchar(14) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `direccion` varchar(100) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_modifico` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cliente`
--

INSERT INTO `cliente` (`idcliente`, `nombres`, `apellidos`, `idtipodoc`, `num_documento`, `telefono`, `email`, `direccion`, `fecha_creacion`, `fecha_modificacion`, `usuario_modifico`) VALUES
(1, 'Juan Miguel', 'Pérez Robles', 1, '1234567890', '0991234561', 'juan.perez@email.com', 'Av. Principal 123', '2025-09-06 17:27:22', '2025-09-06 17:27:22', 1),
(2, 'María Susi', 'Gómez', 2, '100885936001', '0991234562', 'maria.gomez@email.com', 'Calle Secundaria 45', '2025-09-06 17:27:22', '2025-09-06 17:27:22', 1),
(3, 'Carlos Fernando', 'Ramírez', 1, '1122334455', '0991234563', 'carlos.ramirez@email.com', 'Av. Central 78', '2025-09-06 17:27:22', '2025-09-06 17:27:22', 2),
(4, 'Luisa Anastasia', 'Fernández Cerda', 2, '1566778899001', '0991234564', 'luisa.fernandez@email.com', 'Calle Nueva 12', '2025-09-06 17:27:22', '2025-09-06 17:27:22', 2),
(5, 'Pedro Pablo', 'Martínez', 1, '6677889900', '0991234565', 'pedro.martinez@email.com', 'Av. Libertad 34', '2025-09-06 17:27:22', '2025-09-06 17:27:22', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_venta`
--

CREATE TABLE `detalle_venta` (
  `iddetalle_venta` int(11) NOT NULL,
  `idventa` int(11) DEFAULT NULL,
  `idproducto` int(11) NOT NULL,
  `cantidad` int(11) NOT NULL,
  `precio_unit` decimal(10,2) NOT NULL,
  `subtotal` decimal(12,2) GENERATED ALWAYS AS (`cantidad` * `precio_unit`) STORED
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalle_venta`
--

INSERT INTO `detalle_venta` (`iddetalle_venta`, `idventa`, `idproducto`, `cantidad`, `precio_unit`) VALUES
(1, 1, 1, 2, 15.00),
(2, 2, 2, 3, 25.00),
(3, 3, 3, 1, 12.00),
(4, 4, 4, 2, 50.00),
(5, 5, 5, 1, 30.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario`
--

CREATE TABLE `inventario` (
  `idinventario` int(11) NOT NULL,
  `idproducto` int(11) DEFAULT NULL,
  `cantidad_disponible` int(11) DEFAULT 0,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_modifico` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimiento_inventario`
--

CREATE TABLE `movimiento_inventario` (
  `idmovimiento` int(11) NOT NULL,
  `idproducto` int(11) NOT NULL,
  `tipo_movimiento` enum('ENTRADA','SALIDA','AJUSTE') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `referencia` varchar(100) DEFAULT NULL,
  `observacion` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `producto`
--

CREATE TABLE `producto` (
  `idproducto` int(11) NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(256) DEFAULT NULL,
  `stock` int(11) DEFAULT NULL,
  `precio_venta` decimal(10,2) NOT NULL,
  `estado` bit(1) DEFAULT b'1',
  `idproveedor` int(11) DEFAULT NULL,
  `idcategoria` int(11) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_modifico` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `producto`
--

INSERT INTO `producto` (`idproducto`, `codigo`, `nombre`, `descripcion`, `stock`, `precio_venta`, `estado`, `idproveedor`, `idcategoria`, `fecha_creacion`, `fecha_modificacion`, `usuario_modifico`) VALUES
(1, 'P001', 'Uniforme deportivo sublimado', 'En tela deportiva para adultos', 20, 20.00, b'1', 1, 1, '2025-09-06 19:38:06', '2025-09-14 17:14:47', 1),
(2, 'P002', 'Camisa casual para mujer', 'Mouse óptico inalámbrico con receptor USB', 100, 25.00, b'1', 2, 1, '2025-09-06 19:38:06', '2025-09-06 19:38:06', 1),
(3, 'P003', 'Camiseta Tipo Polo unisex', 'Teclado mecánico retroiluminado RGB', 50, 12.00, b'1', 2, 2, '2025-09-06 19:38:06', '2025-09-06 19:38:06', 1),
(4, 'P004', 'Pelotas micasa N° 5', 'Monitor LED Full HD de 24 pulgadas', 15, 50.00, b'1', 1, 3, '2025-09-06 19:38:06', '2025-09-06 19:38:06', 1),
(5, 'P005', 'Overoles', 'Impresora láser monocromática con conexión WiFi', 10, 30.00, b'1', 4, 2, '2025-09-06 19:38:06', '2025-09-06 19:38:06', 1),
(7, 'P006', 'MMM', 'DDDD', 10, 1.00, b'1', NULL, 5, '2025-09-14 15:31:47', '2025-09-14 15:31:47', NULL),
(11, 'P007', 'Bandas', 'rytytyt', 20, 10.00, b'1', NULL, 5, '2025-09-14 16:37:09', '2025-09-14 16:37:09', NULL),
(12, 'P008', 'DDD', 'GHHH', 1, 10.00, b'1', NULL, 4, '2025-09-14 16:38:36', '2025-09-14 16:38:36', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedor`
--

CREATE TABLE `proveedor` (
  `idproveedor` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(100) DEFAULT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `direccion` varchar(100) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `proveedor`
--

INSERT INTO `proveedor` (`idproveedor`, `nombre`, `descripcion`, `telefono`, `direccion`, `ciudad`) VALUES
(1, 'Proveedores Deportivos S.A.', 'Suministro de uniformes y implementos deportivos', '0991234561', 'Av. Principal 123', 'Quito'),
(2, 'Ropa y Textiles del Norte', 'Provisión de ropa casual y formal', '0991234562', 'Calle Secundaria 45', 'Guayaquil'),
(3, 'Uniformes Escolares Ecuatorianos', 'Fabricación de uniformes escolares', '0991234563', 'Av. Central 78', 'Cuenca'),
(4, 'Distribuciones Laborales S.A.', 'Provisión de ropa de trabajo e industrial', '0991234564', 'Calle Nueva 12', 'Ambato'),
(5, 'Medias y Calzado Deportivo', 'Suministro de medias y calzado deportivo', '0991234565', 'Av. Libertad 34', 'Machala');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rol`
--

CREATE TABLE `rol` (
  `idrol` int(11) NOT NULL,
  `nombre` varchar(40) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `estado` tinyint(1) DEFAULT 1 COMMENT '1=Activo, 0=Inactivo'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `rol`
--

INSERT INTO `rol` (`idrol`, `nombre`, `descripcion`, `estado`) VALUES
(1, 'Administrador', 'Usuario con todos los privilegios en el sistema', 1),
(2, 'Vendedor', 'Usuario encargado de registrar ventas y atender clientes', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tipo_documento`
--

CREATE TABLE `tipo_documento` (
  `idtipodoc` int(11) NOT NULL,
  `nombre` varchar(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tipo_documento`
--

INSERT INTO `tipo_documento` (`idtipodoc`, `nombre`) VALUES
(1, 'CÉDULA'),
(2, 'RUC');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `idusuario` int(11) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `idtipodoc` int(11) NOT NULL,
  `num_documento` varchar(14) NOT NULL,
  `telefono` varchar(15) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `direccion` varchar(100) DEFAULT NULL,
  `password_hash` varchar(255) NOT NULL,
  `idrol` int(11) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT current_timestamp(),
  `fecha_modificacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `usuario_modifico` int(11) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT 1 COMMENT '1=Activo, 0=Inactivo',
  `foto` longblob DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`idusuario`, `nombres`, `apellidos`, `idtipodoc`, `num_documento`, `telefono`, `email`, `direccion`, `password_hash`, `idrol`, `fecha_creacion`, `fecha_modificacion`, `usuario_modifico`, `estado`, `foto`) VALUES
(1, 'Salomoón Patricio', 'Licuy Cerda', 1, '1500885916', '0959699642', 'sislitechinfo@gmail.com', 'Av. Pano', 'pbkdf2:sha256:260000$xKzKkSbgA0iU9hhc$497a3bc7d84e9a3d3ff7ff2f22f18ca916d8499ec51f18eab1dfce0c1043f1ac\r\n', 1, '2025-09-06 17:25:46', '2025-09-14 00:08:39', NULL, 1, NULL),
(2, 'Carlos José', 'García Sanchez', 1, '2233445566', '0998765432', 'carlos.garcia@email.com', 'Calle Secundaria 50', 'carlos', 2, '2025-09-06 17:25:46', '2025-09-06 17:25:46', 1, 1, NULL),
(3, 'María Ana', 'Fernández Tapuy', 1, '3344556677', '0997654321', 'maria.fernandez@email.com', 'Av. Central 200', 'hashed_password_maria', 2, '2025-09-06 17:25:46', '2025-09-06 17:25:46', 1, 1, NULL),
(5, 'Salomon Patricio', 'Licuy Cerda', 1, '1500885912', '0959699642', 'salolic90@gmail.com', 'AV. PANO', 'scrypt:32768:8:1$UAKLhtNsICB8HGjz$8c770a054f376d2f1348236e86b2f9290b32071ff830165d1dbf58cb49cdcca011883bc7b35a5a9361f7edffc385592d736bc8228c833a76dc5204e6c9a6ec88', 1, '2025-09-14 00:40:23', '2025-09-14 00:40:23', NULL, 1, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `venta`
--

CREATE TABLE `venta` (
  `idventa` int(11) NOT NULL,
  `idcliente` int(11) DEFAULT NULL,
  `idusuario` int(11) DEFAULT NULL,
  `tipo_comprobante` varchar(20) NOT NULL,
  `fecha_hora` timestamp NOT NULL DEFAULT current_timestamp(),
  `total` decimal(12,2) NOT NULL,
  `estado` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `venta`
--

INSERT INTO `venta` (`idventa`, `idcliente`, `idusuario`, `tipo_comprobante`, `fecha_hora`, `total`, `estado`) VALUES
(1, 1, 1, 'Factura', '2025-09-06 23:12:05', 30.00, 'Completada'),
(2, 2, 2, 'Boleta', '2025-09-06 23:12:05', 75.00, 'Pendiente'),
(3, 3, 1, 'Factura', '2025-09-06 23:12:05', 12.00, 'Completada'),
(4, 1, 3, 'Boleta', '2025-09-06 23:12:05', 100.00, 'Completada'),
(5, 3, 2, 'Factura', '2025-09-06 23:12:05', 30.00, 'Pendiente');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `categoria`
--
ALTER TABLE `categoria`
  ADD PRIMARY KEY (`idcategoria`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD KEY `usuario_modifico` (`usuario_modifico`);

--
-- Indices de la tabla `cliente`
--
ALTER TABLE `cliente`
  ADD PRIMARY KEY (`idcliente`),
  ADD UNIQUE KEY `num_documento` (`num_documento`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idtipodoc` (`idtipodoc`),
  ADD KEY `usuario_modifico` (`usuario_modifico`);

--
-- Indices de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD PRIMARY KEY (`iddetalle_venta`),
  ADD KEY `idventa` (`idventa`),
  ADD KEY `idproducto` (`idproducto`);

--
-- Indices de la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD PRIMARY KEY (`idinventario`),
  ADD UNIQUE KEY `idproducto` (`idproducto`),
  ADD KEY `usuario_modifico` (`usuario_modifico`);

--
-- Indices de la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  ADD PRIMARY KEY (`idmovimiento`),
  ADD KEY `idproducto` (`idproducto`);

--
-- Indices de la tabla `producto`
--
ALTER TABLE `producto`
  ADD PRIMARY KEY (`idproducto`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD KEY `idproveedor` (`idproveedor`),
  ADD KEY `idcategoria` (`idcategoria`),
  ADD KEY `usuario_modifico` (`usuario_modifico`);

--
-- Indices de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  ADD PRIMARY KEY (`idproveedor`);

--
-- Indices de la tabla `rol`
--
ALTER TABLE `rol`
  ADD PRIMARY KEY (`idrol`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `tipo_documento`
--
ALTER TABLE `tipo_documento`
  ADD PRIMARY KEY (`idtipodoc`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`idusuario`),
  ADD UNIQUE KEY `num_documento` (`num_documento`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idrol` (`idrol`),
  ADD KEY `idtipodoc` (`idtipodoc`),
  ADD KEY `usuario_modifico` (`usuario_modifico`);

--
-- Indices de la tabla `venta`
--
ALTER TABLE `venta`
  ADD PRIMARY KEY (`idventa`),
  ADD KEY `idcliente` (`idcliente`),
  ADD KEY `idusuario` (`idusuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `categoria`
--
ALTER TABLE `categoria`
  MODIFY `idcategoria` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `cliente`
--
ALTER TABLE `cliente`
  MODIFY `idcliente` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  MODIFY `iddetalle_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `inventario`
--
ALTER TABLE `inventario`
  MODIFY `idinventario` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  MODIFY `idmovimiento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `producto`
--
ALTER TABLE `producto`
  MODIFY `idproducto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  MODIFY `idproveedor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `rol`
--
ALTER TABLE `rol`
  MODIFY `idrol` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `tipo_documento`
--
ALTER TABLE `tipo_documento`
  MODIFY `idtipodoc` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `idusuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `venta`
--
ALTER TABLE `venta`
  MODIFY `idventa` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `categoria`
--
ALTER TABLE `categoria`
  ADD CONSTRAINT `categoria_ibfk_1` FOREIGN KEY (`usuario_modifico`) REFERENCES `usuario` (`idusuario`);

--
-- Filtros para la tabla `cliente`
--
ALTER TABLE `cliente`
  ADD CONSTRAINT `cliente_ibfk_1` FOREIGN KEY (`idtipodoc`) REFERENCES `tipo_documento` (`idtipodoc`),
  ADD CONSTRAINT `cliente_ibfk_2` FOREIGN KEY (`usuario_modifico`) REFERENCES `usuario` (`idusuario`);

--
-- Filtros para la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD CONSTRAINT `detalle_venta_ibfk_1` FOREIGN KEY (`idventa`) REFERENCES `venta` (`idventa`) ON DELETE CASCADE,
  ADD CONSTRAINT `detalle_venta_ibfk_2` FOREIGN KEY (`idproducto`) REFERENCES `producto` (`idproducto`) ON DELETE CASCADE;

--
-- Filtros para la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD CONSTRAINT `inventario_ibfk_1` FOREIGN KEY (`idproducto`) REFERENCES `producto` (`idproducto`) ON DELETE CASCADE,
  ADD CONSTRAINT `inventario_ibfk_2` FOREIGN KEY (`usuario_modifico`) REFERENCES `usuario` (`idusuario`) ON DELETE SET NULL;

--
-- Filtros para la tabla `movimiento_inventario`
--
ALTER TABLE `movimiento_inventario`
  ADD CONSTRAINT `movimiento_inventario_ibfk_1` FOREIGN KEY (`idproducto`) REFERENCES `producto` (`idproducto`) ON DELETE CASCADE;

--
-- Filtros para la tabla `producto`
--
ALTER TABLE `producto`
  ADD CONSTRAINT `producto_ibfk_1` FOREIGN KEY (`idproveedor`) REFERENCES `proveedor` (`idproveedor`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `producto_ibfk_2` FOREIGN KEY (`idcategoria`) REFERENCES `categoria` (`idcategoria`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `producto_ibfk_3` FOREIGN KEY (`usuario_modifico`) REFERENCES `usuario` (`idusuario`);

--
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `usuario_ibfk_1` FOREIGN KEY (`idrol`) REFERENCES `rol` (`idrol`),
  ADD CONSTRAINT `usuario_ibfk_2` FOREIGN KEY (`idtipodoc`) REFERENCES `tipo_documento` (`idtipodoc`),
  ADD CONSTRAINT `usuario_ibfk_3` FOREIGN KEY (`usuario_modifico`) REFERENCES `usuario` (`idusuario`) ON DELETE SET NULL;

--
-- Filtros para la tabla `venta`
--
ALTER TABLE `venta`
  ADD CONSTRAINT `venta_ibfk_1` FOREIGN KEY (`idcliente`) REFERENCES `cliente` (`idcliente`) ON DELETE SET NULL,
  ADD CONSTRAINT `venta_ibfk_2` FOREIGN KEY (`idusuario`) REFERENCES `usuario` (`idusuario`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
